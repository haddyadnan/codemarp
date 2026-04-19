def package_from_module_id(module_id: str) -> str:
    if "." not in module_id:
        return ""
    return module_id.rsplit(".", 1)[0]
