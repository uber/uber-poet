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
    configs = {{
        "Debug": {{
            "SWIFT_WHOLE_MODULE_OPTIMIZATION": "{2}",
        }},
    }},
    deps = [
        {1}
    ],
)

# xcode_workspace_config(
#     name = "MockApp",
#     extra_schemes = {{
#         {0}
#     }},
#     src_target = ":App",
#     workspace_name = "MockApp",
# )