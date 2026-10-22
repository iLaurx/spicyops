import copy
from django.test import SimpleTestCase
from portal.telemetry import duration, normalize, same_boot, estimate_uptime

def raw(up='100000000/200000000', uptime='1h', identity='Router de test'):
    # Datos sintéticos exclusivos de tests: nunca se cargan en el producto.
    return {'schema':1,'router':{'identity':identity,'version':'6.49.23','uptime':uptime},
        'queues':[{'.id':'*1','name':'Abonado de test','target':'198.51.100.20/32','max-limit':'2M/4M','bytes':up,'rate':'100k/200k'}],
        'restrictions':[], 'raspberry':{}}

class TelemetryTests(SimpleTestCase):
    def test_routeros_duration_formats(self):
        for value, expected in [('1w2d3h4m5s',788645),('1d01:02:03',90123),('2h3m',7380),('1m500ms',60.5)]:
            self.assertEqual(duration(value),expected)
        with self.assertRaises(ValueError): duration('arbitrary')

    def test_limits_are_mbps_and_counters_are_bytes(self):
        result = normalize(raw(),10000)
        row = result['clients'][0]
        self.assertEqual((row['plan_up_mbps'],row['plan_down_mbps']),(2,4))
        self.assertEqual(row['bytes'],300000000)
        self.assertEqual(row['rate_down_mbps'],.2)






    def test_shared_queues_and_infrastructure_are_excluded(self):
        source=raw()
        for target in ['0.0.0.0/0','198.51.100.1/32','198.51.100.50/32','198.51.100.90/32','198.51.100.0/24','198.51.100.20/32,198.51.100.21/32']:
            source['queues'].append({'.id':target,'target':target,'max-limit':'2M/4M'})
        result=normalize(source,10000)
        self.assertEqual(result['excluded'],6)
        self.assertEqual(len(result['clients']),1)

    def test_ambiguous_ip_is_not_double_counted(self):
        source=raw(); second=copy.deepcopy(source['queues'][0]);second['.id']='*2';source['queues'].append(second)
        result=normalize(source,10000)
        self.assertIsNone(result['total_bytes'])
        self.assertTrue(all(c['ambiguous'] for c in result['clients']))

    def test_missing_counters_are_unknown_instead_of_zero(self):
        source=raw();del source['queues'][0]['bytes']
        result=normalize(source,10000)
        self.assertIsNone(result['clients'][0]['bytes'])

    def test_routeros7_and_unlimited_speed(self):
        source=raw();source['router']['version']='7.20.1';source['queues'][0]['max-limit']='0/1G'
        row=normalize(source,10000)['clients'][0]
        self.assertEqual(row['plan_up_mbps'],0)
        self.assertEqual(row['plan_down_mbps'],1000)

    def test_morosos_and_disabled_queue_are_configuration_states(self):
        source=raw();source['restrictions']=[{'list':'Morosos','address':'198.51.100.20','disabled':False}]
        self.assertEqual(normalize(source,10000)['clients'][0]['status'],'Restricción activa')
        source['queues'][0]['disabled']=True
        self.assertEqual(normalize(source,10000)['clients'][0]['status'],'Cola deshabilitada')

    def test_restart_during_read_is_rejected(self):
        source=raw(uptime='1m');source['router']['uptime_start']='1h'
        with self.assertRaises(ValueError):normalize(source,10000)


    def test_uptime_estimate_uses_counter_and_router_uptime(self):
        rows,summary=estimate_uptime([normalize(raw('100/200','1h'),10000)])
        self.assertEqual(rows[0]['daily_bytes'],7200)
        self.assertEqual(rows[0]['monthly_bytes'],216000)
        self.assertEqual(summary['estimated_count'],1)

    def test_uptime_estimate_does_not_use_interval_delta(self):
        a=normalize(raw('100/200','1h'),10000)
        b=normalize(raw('200/400','1h1m'),10060)
        rows,_=estimate_uptime([a,b])
        self.assertAlmostEqual(rows[0]['daily_bytes'],600/3660*86400)

    def test_uptime_estimate_excludes_known_resets_and_new_queues(self):
        a=normalize(raw('100/200','1h'),10000)
        b=normalize(raw('50/400','1h1m'),10060)
        rows,summary=estimate_uptime([a,b])
        self.assertIsNone(rows[0]['daily_bytes'])
        self.assertFalse(summary['ready'])
        a['clients']=[]
        rows,_=estimate_uptime([a,b])
        self.assertIsNone(rows[0]['monthly_bytes'])

    def test_uptime_estimate_waits_for_minimum_time_and_known_counter(self):
        for source in [raw(uptime='30s'),raw()]:
            if source['router']['uptime']=='1h': del source['queues'][0]['bytes']
            rows,summary=estimate_uptime([normalize(source,10000)])
            self.assertIsNone(rows[0]['daily_bytes'])
            self.assertFalse(summary['ready'])
        self.assertEqual(estimate_uptime([])[0],[])

    def test_estimate_keeps_latest_order_and_history_unchanged(self):
        a = normalize(raw('100/200', '1h'), 10000)
        b = normalize(raw('200/400', '1h1m'), 10060)
        for sample in (a, b):
            sample['clients'].append(dict(sample['clients'][0], id='*2', fingerprint='other'))
        b['clients'].reverse()
        original = copy.deepcopy([a, b])
        rows, summary = estimate_uptime([a, b])
        self.assertEqual([r['fingerprint'] for r in rows], ['other', a['clients'][0]['fingerprint']])
        self.assertEqual(summary['estimated_count'], 2)
        self.assertEqual([a, b], original)

    def test_estimate_nearest_invalid_read_determines_note(self):
        missing = normalize(raw('100/200', '1h'), 10000)
        reset = normalize(raw('900/200', '1h1m'), 10060)
        latest = normalize(raw('200/400', '1h2m'), 10120)
        missing['clients'] = []
        rows, _ = estimate_uptime([missing, reset, latest])
        self.assertEqual(rows[0]['estimate_note'], 'Contador reiniciado; edad desconocida')
        reset['clients'] = []
        rows, _ = estimate_uptime([missing, reset, latest])
        self.assertEqual(rows[0]['estimate_note'], 'Cola nueva o modificada; edad del contador desconocida')

    def test_estimate_stops_at_boot_boundary_and_compares_both_directions(self):
        a = normalize(raw('900/200', '1h'), 10000)
        b = normalize(raw('200/400', '1h1m'), 10060)
        # El total crece pero la subida disminuye: sigue siendo un reset.
        rows, _ = estimate_uptime([a, b])
        self.assertIsNone(rows[0]['daily_bytes'])
        a['identity'] = 'Router anterior'
        rows, _ = estimate_uptime([a, b])
        self.assertAlmostEqual(rows[0]['daily_bytes'], 600/3660*86400)

    def test_estimate_unknown_previous_counter_and_ambiguous_priority(self):
        a = normalize(raw('100/200', '1h'), 10000)
        b = normalize(raw('200/400', '1h1m'), 10060)
        a['clients'][0].update(upload_bytes=None, download_bytes=None, bytes=None)
        rows, _ = estimate_uptime([a, b])
        self.assertIsNotNone(rows[0]['daily_bytes'])
        b['uptime'] = 30
        b['clients'][0].update(ambiguous=True, bytes=None)
        rows, _ = estimate_uptime([a, b])
        self.assertEqual(rows[0]['estimate_note'], 'Cola ambigua')
