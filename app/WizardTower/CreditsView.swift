import SwiftUI

/// Attribution for the assets whose licences require it.
///
/// Everything else in the room is CC0 and asks for nothing. The animated candle
/// flame is CC BY 4.0, which obliges us to credit its author — so this screen
/// exists, and `assets/ASSET_MANIFEST.md` points at it. Anything added later
/// under an attribution licence belongs in both places.
struct CreditsView: View {

    private struct Credit: Identifiable {
        let id = UUID()
        let work: String
        let author: String
        let licence: String
        let url: String
    }

    private let credits = [
        Credit(work: "Candle light",
               author: "al0sral0",
               licence: "CC BY 4.0",
               url: "https://sketchfab.com/3d-models/candle-light-d9d5ed5de83b4d899ab93f55bdc3d0bc"),
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("Credits")
                .font(.largeTitle)

            ForEach(credits) { credit in
                VStack(alignment: .leading, spacing: 4) {
                    Text("“\(credit.work)” by \(credit.author)")
                        .font(.headline)
                    Text(credit.licence)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Link(credit.url, destination: URL(string: credit.url)!)
                        .font(.caption)
                }
            }

            Text("Every other asset is CC0 and requires no attribution.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .padding(32)
        .frame(maxWidth: 560, alignment: .leading)
    }
}
