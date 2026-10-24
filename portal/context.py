from .version import VERSION

def release(request):
    from .store import storage_warning
    return {"app_version": VERSION, "storage_warning": storage_warning}
