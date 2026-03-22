import nicegui_builder as ngb


def test_stable_api_names_are_exported():
    for name in ngb.STABLE_API:
        assert hasattr(ngb, name), name


def test_experimental_namespaces_are_declared():
    assert ngb.EXPERIMENTAL_NAMESPACES == (
        "nicegui_builder.core",
        "nicegui_builder.plugins",
    )
