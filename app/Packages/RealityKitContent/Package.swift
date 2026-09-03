// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "RealityKitContent",
    platforms: [
        .visionOS(.v1),
        .macOS(.v14),
        .iOS(.v17)
    ],
    products: [
        .library(
            name: "RealityKitContent",
            targets: ["RealityKitContent"])
    ],
    targets: [
        .target(
            name: "RealityKitContent")
    ]
)
