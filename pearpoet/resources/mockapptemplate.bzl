# xcode_workspace_config(
#     name = "MockApp",
#     extra_schemes = {{
#         {0}
#     }},
#     src_target = ":App",
#     workspace_name = "MockApp",
# )

apple_bundle(
    name = "App",
    binary = ":AppBinary",
    extension = "app",
    info_plist = "Info.plist",
)

apple_binary(
    name = "AppBinary",
    srcs = [
        "main.swift",
    ],
    is_universal = True,
    system_frameworks = [
        "Foundation",
        "UIKit",
    ],
    deps = [
        {1}
    ],
)
