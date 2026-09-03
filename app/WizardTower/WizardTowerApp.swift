import SwiftUI

@main
struct WizardTowerApp: App {

    @State private var appModel = AppModel()

    var body: some Scene {
        WindowGroup(id: AppModel.controlPanelID) {
            ControlPanelView()
                .environment(appModel)
        }
        .windowResizability(.contentSize)
        .defaultSize(width: 420, height: 260)

        ImmersiveSpace(id: AppModel.immersiveSpaceID) {
            TowerImmersiveView()
                .environment(appModel)
        }
        .immersionStyle(selection: $appModel.immersionStyle, in: .mixed, .progressive, .full)
    }
}
