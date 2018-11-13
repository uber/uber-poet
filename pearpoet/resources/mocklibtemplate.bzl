apple_library(
    name = "{0}",
    srcs = glob([
        "Sources/*.swift",
    ]),
    system_frameworks = [
        "Foundation",
        "UIKit",
    ],
    tests = [],
    visibility = [
        "PUBLIC",
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
#     name = "{0}Scheme",
#     src_target = ":{0}",
#     visibility = [
#         "PUBLIC",
#     ],
# )
