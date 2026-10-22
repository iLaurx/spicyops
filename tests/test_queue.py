from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import threading
from django.core.exceptions import PermissionDenied
from django.db import connection, connections, transaction
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from ops.models import Agent, Attempt, Membership, Plan, Router, Service, Task
from ops.queue import authenticate, claim, report, request_action, validate_execution
from .support import fixture

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class QueueTests(TransactionTestCase):
    def setUp(self): self.f = fixture()
    def request(self, action='provision', **kwargs):
        service = Service.objects.get(pk=self.f['service'].pk)
        return request_action(self.f['user'], service.pk, action, kwargs.get('plan'), 'Prueba ficticia', service.revision)
    def provision(self):
        task = self.request()
        item = claim(self.f['agent'])
        self.assertEqual(report(self.f['agent'], task.pk, item['attempt'], {'ok': True, 'state': item['state'], 'error': ''}), 'accepted')

    def test_postgresql_is_the_backend(self):
        self.assertEqual(connection.vendor, 'postgresql')
        with connection.cursor() as cursor:
            cursor.execute('SHOW server_version')
            self.assertTrue(cursor.fetchone()[0])

    def test_intent_does_not_mark_observed_before_result(self):
        task = self.request()
        service = Service.objects.get(pk=task.service_id)
        self.assertTrue(service.desired_enabled)
        self.assertEqual(service.observed, {})
        item = claim(self.f['agent'])
        self.assertEqual(report(self.f['agent'], task.pk, item['attempt'], {'ok': True, 'state': item['state'], 'error': ''}), 'accepted')
        service.refresh_from_db()
        self.assertEqual(service.observed, item['state'])

    def test_invalid_action_rolls_back_revision(self):
        with self.assertRaises(ValueError): self.request('arbitrary-command')
        self.assertEqual(Service.objects.get(pk=self.f['service'].pk).revision, 0)
        self.assertEqual(Task.objects.count(), 0)

    def test_stale_browser_revision_rejected(self):
        self.request()
        with self.assertRaises(ValueError):
            request_action(self.f['user'], self.f['service'].pk, 'provision', None, 'Duplicada', 0)
        self.assertEqual(Task.objects.count(), 1)

    def test_obsolete_and_expired_tasks_never_claimed(self):
        old = self.request()
        newer = self.request()
        Task.objects.filter(pk=newer.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertIsNone(claim(self.f['agent']))
        old.refresh_from_db(); newer.refresh_from_db()
        self.assertEqual(old.status, 'obsolete')
        self.assertEqual(newer.status, 'expired')

    def test_two_postgres_consumers_get_one_lease(self):
        self.request()
        barrier = threading.Barrier(2)
        def consumer():
            try:
                with connections['default'].cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pid = cursor.fetchone()[0]
                agent = Agent.objects.get(pk=self.f['agent'].pk)
                barrier.wait(timeout=10)
                return pid, claim(agent)
            finally: connections['default'].close()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: consumer(), range(2)))
        self.assertNotEqual(results[0][0], results[1][0])
        self.assertEqual(sum(result is not None for _, result in results), 1)
        self.assertEqual(Attempt.objects.count(), 1)

    def test_locked_router_is_skipped_by_other_connection(self):
        self.request()
        with transaction.atomic():
            Router.objects.select_for_update().get(pk=self.f['router'].pk)
            def consumer():
                try: return claim(Agent.objects.get(pk=self.f['agent'].pk))
                finally: connections['default'].close()
            with ThreadPoolExecutor(max_workers=1) as pool:
                self.assertIsNone(pool.submit(consumer).result(timeout=10))
        self.assertIsNotNone(claim(self.f['agent']))

    def test_serialization_is_per_router_even_for_two_services(self):
        self.request()
        second = Service.objects.create(customer=self.f['customer'], router=self.f['router'], plan=self.f['plan'], ip='198.51.100.21', location='Otra casa')
        request_action(self.f['user'], second.pk, 'provision', None, 'Alta', 0)
        self.assertIsNotNone(claim(self.f['agent']))
        self.assertIsNone(claim(self.f['agent']))

    def test_lost_lease_retries_with_new_attempt_and_rejects_old_report(self):
        task = self.request()
        old = claim(self.f['agent'])
        Task.objects.filter(pk=task.pk).update(lease_until=timezone.now()-timedelta(seconds=1))
        new = claim(self.f['agent'])
        self.assertNotEqual(new['attempt'], old['attempt'])
        self.assertEqual(report(self.f['agent'], task.pk, old['attempt'], {'ok': True, 'state': old['state'], 'error': ''}), 'conflict')
        self.assertEqual(Service.objects.get(pk=task.service_id).observed, {})
        self.assertEqual(Attempt.objects.count(), 2)

    def test_report_and_validate_reject_newer_revision(self):
        self.request()
        old = claim(self.f['agent'])
        self.request()
        self.assertIsNone(validate_execution(self.f['agent'], old['task'], old['attempt']))
        self.assertEqual(report(self.f['agent'], old['task'], old['attempt'], {'ok': True, 'state': old['state'], 'error': ''}), 'conflict')
        self.assertIsNone(claim(self.f['agent']))  # conserva concesión anterior hasta vencer

    def test_repeated_report_deduplicated_and_modified_report_rejected(self):
        task = self.request(); item = claim(self.f['agent'])
        body = {'ok': True, 'state': item['state'], 'error': ''}
        self.assertEqual(report(self.f['agent'], task.pk, item['attempt'], body), 'accepted')
        self.assertEqual(report(self.f['agent'], task.pk, item['attempt'], body), 'duplicate')
        self.assertEqual(report(self.f['agent'], task.pk, item['attempt'], {'ok': False, 'state': None, 'error': 'execution_failed'}), 'conflict')

    def test_forged_success_does_not_change_observed(self):
        task = self.request(); item = claim(self.f['agent'])
        wrong = dict(item['state'], down_kbps=999)
        with self.assertRaises(ValueError): report(self.f['agent'], task.pk, item['attempt'], {'ok': True, 'state': wrong, 'error': ''})
        self.assertEqual(Service.objects.get(pk=task.service_id).observed, {})

    def test_retries_have_backoff_and_limit(self):
        task = self.request()
        for number in range(5):
            Task.objects.filter(pk=task.pk).update(available_at=timezone.now()-timedelta(seconds=1))
            item = claim(self.f['agent'])
            self.assertIsNotNone(item)
            report(self.f['agent'], task.pk, item['attempt'], {'ok': False, 'state': None, 'error': 'execution_failed'})
            self.assertIsNone(claim(self.f['agent']))
        task.refresh_from_db()
        self.assertEqual(task.status, 'verification')
        self.assertEqual(task.attempts, 5)

    def test_authorization_site_viewer_and_revoked_agent(self):
        other = fixture('b')
        with self.assertRaises(PermissionDenied):
            request_action(other['user'], self.f['service'].pk, 'provision', None, 'Intrusión', 0)
        Membership.objects.filter(user=self.f['user']).update(role='viewer')
        with self.assertRaises(PermissionDenied): self.request()
        with self.assertRaises(PermissionDenied): authenticate(self.f['agent'].pk, 'incorrecto')
        Agent.objects.filter(pk=self.f['agent'].pk).update(active=False)
        with self.assertRaises(PermissionDenied): authenticate(self.f['agent'].pk, self.f['token'])

    def test_other_site_cannot_claim_validate_or_report(self):
        self.request(); other = fixture('b')
        self.assertIsNone(claim(other['agent']))
        item = claim(self.f['agent'])
        with self.assertRaises(PermissionDenied): validate_execution(other['agent'], item['task'], item['attempt'])
        with self.assertRaises(PermissionDenied): report(other['agent'], item['task'], item['attempt'], {})

    def test_infrastructure_and_cross_site_plan_rejected(self):
        Service.objects.filter(pk=self.f['service'].pk).update(ip='198.51.100.1')
        with self.assertRaises(ValueError): self.request()
        self.assertEqual(Task.objects.count(), 0)
        Service.objects.filter(pk=self.f['service'].pk).update(ip='198.51.100.20')
        self.provision()
        other = fixture('b')
        with self.assertRaises(Plan.DoesNotExist): self.request('plan', plan=other['plan'].pk)
        self.assertEqual(Service.objects.get(pk=self.f['service'].pk).plan_id, self.f['plan'].pk)

    def test_free_plan_suspension_blocked(self):
        self.provision()
        self.f['plan'].commercial_free = True; self.f['plan'].save()
        with self.assertRaises(ValueError): self.request('suspend')

    def test_fresh_connections_keep_pending_and_result(self):
        task = self.request()
        connection.close()
        self.assertEqual(Task.objects.get(pk=task.pk).status, 'pending')
        item = claim(self.f['agent'])
        report(self.f['agent'], task.pk, item['attempt'], {'ok': True, 'state': item['state'], 'error': ''})
        connection.close()
        self.assertEqual(Task.objects.get(pk=task.pk).status, 'verified')
        self.assertEqual(Service.objects.get(pk=task.service_id).observed, item['state'])
