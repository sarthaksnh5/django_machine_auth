from rest_framework.throttling import SimpleRateThrottle


class MachineAPIKeyRateThrottle(SimpleRateThrottle):
    scope = "machine_api_key"

    def get_cache_key(self, request, view):
        api_key = getattr(request, "machine_api_key", None)
        if not api_key:
            return self.get_ident(request)
        return f"machine_api_key:{getattr(api_key, 'id', 'unknown')}"
