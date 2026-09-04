import CoreGraphics
import Foundation

/// A sky computed rather than photographed.
///
/// The room already knows exactly where the sun is -- `SolarPosition` works it
/// out from the date, the hour and the latitude. A photographic HDRI cannot use
/// that: its sun is baked in wherever it happened to be when the picture was
/// taken, so the light raking through the window and the sun visible through it
/// disagree, and there are only three of them to cut between.
///
/// This takes the same sun vector the lights use, so the two agree by
/// construction and move continuously through the day.
///
/// Daylight is the Preetham analytic model (A Practical Analytic Model for
/// Daylight, SIGGRAPH 1999): a Perez sky-luminance distribution fitted to
/// turbidity, evaluated in CIE xyY and converted to sRGB. Below the horizon it
/// crosses into a night sky of its own with stars and a moon.
struct SkyModel: Equatable {

    /// Degrees above the horizon.
    var sunElevation: Float
    /// Degrees clockwise from straight ahead (the desk), matching the room's
    /// convention: the window is at +55.
    var sunAzimuth: Float
    /// Haze. 2 is an alpine day, 6 is a warm humid one.
    var turbidity: Float = 2.7
    /// 0 is clear, 1 is overcast.
    var cloudCover: Float = 0.42
    /// Scales the model's cd/m² into something the tone curve can use. Tuned so
    /// midday matches the brightness of the HDRI it replaced.
    var exposure: Float = 0.055

    // MARK: - Perez

    /// F(theta, gamma) -- the Perez distribution shared by luminance and both
    /// chromaticity channels.
    private static func perez(_ cosTheta: Float, _ gamma: Float,
                              _ a: Float, _ b: Float, _ c: Float,
                              _ d: Float, _ e: Float) -> Float {
        // Guard the horizon: cos(theta) reaches 0 there and the exponential runs away.
        let ct = max(cosTheta, 0.01)
        let cosGamma = cos(gamma)
        return (1.0 + a * exp(b / ct))
             * (1.0 + c * exp(d * gamma) + e * cosGamma * cosGamma)
    }

    private struct Coefficients {
        var a, b, c, d, e: Float
    }

    private func luminanceCoefficients(_ t: Float) -> Coefficients {
        Coefficients(a:  0.1787 * t - 1.4630, b: -0.3554 * t + 0.4275,
                     c: -0.0227 * t + 5.3251, d:  0.1206 * t - 2.5771,
                     e: -0.0670 * t + 0.3703)
    }

    private func xCoefficients(_ t: Float) -> Coefficients {
        Coefficients(a: -0.0193 * t - 0.2592, b: -0.0665 * t + 0.0008,
                     c: -0.0004 * t + 0.2125, d: -0.0641 * t - 0.8989,
                     e: -0.0033 * t + 0.0452)
    }

    private func yCoefficients(_ t: Float) -> Coefficients {
        Coefficients(a: -0.0167 * t - 0.2608, b: -0.0950 * t + 0.0092,
                     c: -0.0079 * t + 0.2102, d: -0.0441 * t - 1.6537,
                     e: -0.0109 * t + 0.0529)
    }

    /// Zenith luminance and chromaticity for a given turbidity and solar zenith.
    private func zenith(_ t: Float, _ thetaS: Float) -> (Y: Float, x: Float, y: Float) {
        let chi = (4.0 / 9.0 - t / 120.0) * (.pi - 2.0 * thetaS)
        let yZ = (4.0453 * t - 4.9710) * tan(chi) - 0.2155 * t + 2.4192

        let s = thetaS, s2 = thetaS * thetaS, s3 = s2 * thetaS
        let t2 = t * t
        let xZ =
            t2 * ( 0.00166 * s3 - 0.00375 * s2 + 0.00209 * s + 0.0)
          + t  * (-0.02903 * s3 + 0.06377 * s2 - 0.03202 * s + 0.00394)
          +      ( 0.11693 * s3 - 0.21196 * s2 + 0.06052 * s + 0.25886)
        let yy =
            t2 * ( 0.00275 * s3 - 0.00610 * s2 + 0.00317 * s + 0.0)
          + t  * (-0.04214 * s3 + 0.08970 * s2 - 0.04153 * s + 0.00516)
          +      ( 0.15346 * s3 - 0.26756 * s2 + 0.06670 * s + 0.26688)
        return (max(yZ, 0.0), xZ, yy)
    }

    // MARK: - Noise, for the clouds and the stars

    private static func hash(_ x: Int, _ y: Int, _ z: Int) -> Float {
        var h = UInt32(truncatingIfNeeded: x &* 374_761_393
                                        &+ y &* 668_265_263
                                        &+ z &* 2_147_483_647)
        h = (h ^ (h >> 13)) &* 1_274_126_177
        h = h ^ (h >> 16)
        return Float(h) / Float(UInt32.max)
    }

    private static func valueNoise(_ p: (Float, Float, Float)) -> Float {
        let xi = floor(p.0), yi = floor(p.1), zi = floor(p.2)
        let xf = p.0 - xi, yf = p.1 - yi, zf = p.2 - zi
        // Smoothstep the interpolants so the octaves do not show their lattice.
        let u = xf * xf * (3 - 2 * xf)
        let v = yf * yf * (3 - 2 * yf)
        let w = zf * zf * (3 - 2 * zf)
        let ix = Int(xi), iy = Int(yi), iz = Int(zi)

        func corner(_ dx: Int, _ dy: Int, _ dz: Int) -> Float {
            hash(ix + dx, iy + dy, iz + dz)
        }
        let x00 = corner(0,0,0) + (corner(1,0,0) - corner(0,0,0)) * u
        let x10 = corner(0,1,0) + (corner(1,1,0) - corner(0,1,0)) * u
        let x01 = corner(0,0,1) + (corner(1,0,1) - corner(0,0,1)) * u
        let x11 = corner(0,1,1) + (corner(1,1,1) - corner(0,1,1)) * u
        let y0 = x00 + (x10 - x00) * v
        let y1 = x01 + (x11 - x01) * v
        return y0 + (y1 - y0) * w
    }

    private static func fbm(_ p: (Float, Float, Float), octaves: Int) -> Float {
        var total: Float = 0, amplitude: Float = 0.5, frequency: Float = 1
        var norm: Float = 0
        for _ in 0..<octaves {
            total += valueNoise((p.0 * frequency, p.1 * frequency, p.2 * frequency))
                   * amplitude
            norm += amplitude
            amplitude *= 0.5
            frequency *= 2.07      // not exactly 2, to avoid the octaves aligning
        }
        return total / norm
    }

    private static func smoothstep(_ a: Float, _ b: Float, _ x: Float) -> Float {
        guard b != a else { return x < a ? 0 : 1 }
        let t = min(max((x - a) / (b - a), 0), 1)
        return t * t * (3 - 2 * t)
    }

    // MARK: - Rendering

    /// An equirectangular image of the whole sphere.
    ///
    /// The same image feeds both the visible dome and the image-based light, so
    /// what the room is lit by is by definition what is out of the window.
    /// 2048 wide is not about detail in the gradient -- that would be fine at a
    /// quarter of it -- but about the stars. One pixel of a 1024-wide
    /// equirectangular map subtends 0.35 degrees on the dome, which is roughly
    /// the angular size of the moon, so single-pixel stars came out as blobs the
    /// size of the moon. Halving the pixel angle, and dimming them so the
    /// bilinear filter has less to smear, brings them back to points.
    func image(width: Int = 2048, height: Int = 1024) -> CGImage? {
        let elevation = sunElevation * .pi / 180.0
        let azimuth = sunAzimuth * .pi / 180.0

        // Room convention: +Y up, -Z straight ahead, +X to the right.
        let sun = (x: cos(elevation) * sin(azimuth),
                   y: sin(elevation),
                   z: -cos(elevation) * cos(azimuth))

        // Preetham is only defined for a sun at or above the horizon. Hold it
        // there and fade the whole daylight term out through twilight instead.
        let thetaS = min(max(.pi / 2.0 - elevation, 0.0), .pi / 2.0 - 0.001)
        let lum = luminanceCoefficients(turbidity)
        let cx = xCoefficients(turbidity)
        let cy = yCoefficients(turbidity)
        let z = zenith(turbidity, thetaS)
        let fZeroY = Self.perez(1.0, thetaS, lum.a, lum.b, lum.c, lum.d, lum.e)
        let fZeroX = Self.perez(1.0, thetaS, cx.a, cx.b, cx.c, cx.d, cx.e)
        let fZeroYc = Self.perez(1.0, thetaS, cy.a, cy.b, cy.c, cy.d, cy.e)

        let daylight = Self.smoothstep(-12.0, 0.0, sunElevation)
        let starlight = 1.0 - Self.smoothstep(-14.0, -3.0, sunElevation)
        // A full moon rides opposite the sun, which is also exactly where it is
        // useful: highest in the middle of the night.
        let moon = (x: -sun.x, y: -sun.y, z: -sun.z)

        var pixels = [UInt8](repeating: 0, count: width * height * 4)

        for py in 0..<height {
            let v = (Float(py) + 0.5) / Float(height)
            let theta = v * .pi                    // 0 at the zenith
            let sinTheta = sin(theta), cosTheta = cos(theta)

            for px in 0..<width {
                let u = (Float(px) + 0.5) / Float(width)
                let phi = u * 2.0 * .pi
                let dir = (x: sinTheta * sin(phi),
                           y: cosTheta,
                           z: -sinTheta * cos(phi))

                let cosGamma = min(max(dir.x * sun.x + dir.y * sun.y + dir.z * sun.z,
                                       -1), 1)
                let gamma = acos(cosGamma)

                // --- daylight ---
                var rgb: (Float, Float, Float) = (0, 0, 0)
                if daylight > 0.001 {
                    let fY = Self.perez(cosTheta, gamma, lum.a, lum.b, lum.c, lum.d, lum.e)
                    let fX = Self.perez(cosTheta, gamma, cx.a, cx.b, cx.c, cx.d, cx.e)
                    let fYc = Self.perez(cosTheta, gamma, cy.a, cy.b, cy.c, cy.d, cy.e)
                    let Y = z.Y * fY / fZeroY
                    let xc = z.x * fX / fZeroX
                    let yc = z.y * fYc / fZeroYc
                    if yc > 0.0001 {
                        let bigY = max(Y, 0) * exposure
                        let bigX = xc / yc * bigY
                        let bigZ = (1 - xc - yc) / yc * bigY
                        rgb = (
                             3.2406 * bigX - 1.5372 * bigY - 0.4986 * bigZ,
                            -0.9689 * bigX + 1.8758 * bigY + 0.0415 * bigZ,
                             0.0557 * bigX - 0.2040 * bigY + 1.0570 * bigZ)
                    }
                    // The sun itself, with a little bloom around it.
                    let disc = 1.0 - Self.smoothstep(0.004, 0.010, gamma)
                    let glow = pow(max(0, cosGamma), 900) * 0.7
                    let s = disc * 14.0 + glow
                    rgb = (rgb.0 + s, rgb.1 + s * 0.97, rgb.2 + s * 0.90)
                    rgb = (rgb.0 * daylight, rgb.1 * daylight, rgb.2 * daylight)
                }

                // --- night ---
                if starlight > 0.001 {
                    // Deep blue overhead easing to a paler, hazier horizon.
                    let horizon = 1.0 - abs(dir.y)
                    var night: (Float, Float, Float) = (
                        0.008 + 0.020 * horizon,
                        0.013 + 0.026 * horizon,
                        0.030 + 0.042 * horizon)

                    if dir.y > -0.05 {
                        // Stars: one lattice cell per candidate, so they stay put
                        // frame to frame and do not crawl as the sun moves.
                        let sx = Int(dir.x * 3100), sy = Int(dir.y * 3100), sz = Int(dir.z * 3100)
                        let r = Self.hash(sx, sy, sz)
                        if r > 0.9986 {
                            // A second, independent hash for brightness, so the
                            // bright stars are not the ones that happen to sit
                            // highest in the placement lattice.
                            let mag = Self.hash(sz &+ 7, sx &+ 11, sy &+ 13)
                            let b = 0.10 + 0.55 * mag * mag
                            night = (night.0 + b, night.1 + b, night.2 + b * 1.05)
                        }
                    }

                    let cosMoon = dir.x * moon.x + dir.y * moon.y + dir.z * moon.z
                    if cosMoon > 0 {
                        let mg = acos(min(cosMoon, 1))
                        let disc = 1.0 - Self.smoothstep(0.008, 0.013, mg)
                        let halo = pow(cosMoon, 2200) * 0.35
                        let m = disc * 1.5 + halo
                        night = (night.0 + m * 0.95, night.1 + m * 0.97, night.2 + m)
                    }

                    rgb = (rgb.0 + night.0 * starlight,
                           rgb.1 + night.1 * starlight,
                           rgb.2 + night.2 * starlight)
                }

                // --- clouds ---
                if cloudCover > 0.001 && dir.y > -0.02 {
                    // Project onto a shell so the deck recedes toward the
                    // horizon. The divisor has to be floored: 1/y runs away as
                    // y approaches 0 and smears the noise into vertical
                    // curtains along the horizon.
                    let shell = 1.0 / max(dir.y, 0.10)
                    let p = (dir.x * shell * 1.1, dir.y * 1.0, dir.z * shell * 1.1)
                    let n = Self.fbm(p, octaves: 4)
                    let threshold = 1.0 - cloudCover
                    var d = Self.smoothstep(threshold - 0.02, threshold + 0.24, n)
                    // Fade out well before the rim. Clamping the shell instead
                    // does not work: it makes every pixel in a column sample the
                    // same noise, which is exactly what turns the deck into
                    // vertical curtains. Real cloud decks lose themselves in haze
                    // near the horizon anyway.
                    d *= Self.smoothstep(0.14, 0.45, dir.y)

                    if d > 0.001 {
                        // Lit from the sun side, grey where they self-shadow.
                        let toSun = min(max(cosGamma, 0), 1)
                        let litness = 0.45 + 0.55 * pow(toSun, 2.0)
                        let base = 0.85 * daylight + 0.05 * starlight
                        let c = base * litness
                        let cloud = (c, c * 0.99, c * 0.97)
                        rgb = (rgb.0 + (cloud.0 - rgb.0) * d,
                               rgb.1 + (cloud.1 - rgb.1) * d,
                               rgb.2 + (cloud.2 - rgb.2) * d)
                    }
                }

                // --- ground half of the sphere ---
                if dir.y < 0 {
                    // Real terrain covers most of this; what shows past it should
                    // read as land lost in haze. Deriving it from the sky colour
                    // just above rather than from a fixed grey means there is no
                    // seam at the horizon and it stays warm at sunset.
                    let t = Self.smoothstep(0.0, -0.35, dir.y)
                    let g: (Float, Float, Float) = (
                        rgb.0 * 0.30 + 0.020 * daylight + 0.004 * starlight,
                        rgb.1 * 0.30 + 0.021 * daylight + 0.005 * starlight,
                        rgb.2 * 0.30 + 0.017 * daylight + 0.008 * starlight)
                    rgb = (rgb.0 + (g.0 - rgb.0) * t,
                           rgb.1 + (g.1 - rgb.1) * t,
                           rgb.2 + (g.2 - rgb.2) * t)
                }

                let i = (py * width + px) * 4
                pixels[i + 0] = Self.encode(rgb.0)
                pixels[i + 1] = Self.encode(rgb.1)
                pixels[i + 2] = Self.encode(rgb.2)
                pixels[i + 3] = 255
            }
        }

        return Self.makeImage(pixels, width: width, height: height)
    }

    /// Reinhard, then the sRGB transfer curve. Rolling the highlights off keeps
    /// the sun from clipping to a flat white plate.
    private static func encode(_ linear: Float) -> UInt8 {
        let v = max(linear, 0)
        let mapped = v / (1.0 + v)
        let s = mapped <= 0.0031308
            ? 12.92 * mapped
            : 1.055 * pow(mapped, 1.0 / 2.4) - 0.055
        return UInt8(min(max(s, 0), 1) * 255 + 0.5)
    }

    private static func makeImage(_ pixels: [UInt8], width: Int, height: Int) -> CGImage? {
        var data = pixels
        guard let provider = CGDataProvider(data: Data(bytes: &data,
                                                       count: data.count) as CFData),
              let space = CGColorSpace(name: CGColorSpace.sRGB) else { return nil }
        return CGImage(width: width, height: height,
                       bitsPerComponent: 8, bitsPerPixel: 32,
                       bytesPerRow: width * 4,
                       space: space,
                       bitmapInfo: CGBitmapInfo(rawValue:
                           CGImageAlphaInfo.noneSkipLast.rawValue),
                       provider: provider, decode: nil,
                       shouldInterpolate: true, intent: .defaultIntent)
    }
}
