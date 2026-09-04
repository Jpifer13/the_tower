import Foundation

/// Where the sun actually is, for a date, place and clock.
///
/// NOAA's solar position approximation. Good to well under a degree, which is far
/// more than a window needs, and it means the light rakes across the room at the
/// right hours instead of following an invented arc.
struct SolarPosition {

    /// Degrees above the horizon. Negative after sunset.
    let elevation: Double
    /// Degrees clockwise from true north.
    let azimuth: Double

    static func at(_ date: Date,
                   latitude: Double,
                   longitude: Double,
                   timeZone: TimeZone) -> SolarPosition {

        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = timeZone
        let parts = calendar.dateComponents([.dayOfYear, .hour, .minute, .second], from: date)
        let dayOfYear = Double(parts.dayOfYear ?? 1)
        let hour = Double(parts.hour ?? 0)
        let minute = Double(parts.minute ?? 0)
        let second = Double(parts.second ?? 0)

        let rad = Double.pi / 180.0
        let daysInYear = calendar.range(of: .day, in: .year, for: date)?.count == 366 ? 366.0 : 365.0

        // Fractional year, radians.
        let g = 2.0 * .pi / daysInYear * (dayOfYear - 1.0 + (hour - 12.0) / 24.0)

        // Equation of time, minutes; and solar declination, radians.
        let eqTime = 229.18 * (0.000075
            + 0.001868 * cos(g) - 0.032077 * sin(g)
            - 0.014615 * cos(2 * g) - 0.040849 * sin(2 * g))
        let decl = 0.006918
            - 0.399912 * cos(g) + 0.070257 * sin(g)
            - 0.006758 * cos(2 * g) + 0.000907 * sin(2 * g)
            - 0.002697 * cos(3 * g) + 0.00148 * sin(3 * g)

        // True solar time, then the hour angle.
        let tzOffsetHours = Double(timeZone.secondsFromGMT(for: date)) / 3600.0
        let timeOffset = eqTime + 4.0 * longitude - 60.0 * tzOffsetHours
        let trueSolarMinutes = hour * 60.0 + minute + second / 60.0 + timeOffset
        let hourAngle = trueSolarMinutes / 4.0 - 180.0

        let latRad = latitude * rad
        let haRad = hourAngle * rad

        let cosZenith = sin(latRad) * sin(decl) + cos(latRad) * cos(decl) * cos(haRad)
        let zenith = acos(min(1.0, max(-1.0, cosZenith)))
        let elevation = 90.0 - zenith / rad

        var azimuth = 0.0
        let denominator = cos(latRad) * sin(zenith)
        if abs(denominator) > 1e-9 {
            let cosAz = (sin(latRad) * cos(zenith) - sin(decl)) / denominator
            azimuth = acos(min(1.0, max(-1.0, cosAz))) / rad
            // Before solar noon the sun is in the east.
            azimuth = hourAngle > 0 ? 360.0 - azimuth : azimuth
        }
        return SolarPosition(elevation: elevation, azimuth: azimuth)
    }

    /// Which sky to hang outside, from how high the sun is.
    /// Civil twilight is 0 to -6 degrees; golden light lingers a little above that.
    var impliedTimeOfDay: TimeOfDay {
        if elevation > 6.0 { return .day }
        if elevation > -6.0 { return .sunset }
        return .night
    }

    /// 0 at and below the horizon, easing to 1 by mid-morning. Keeps the sun from
    /// snapping on at sunrise.
    var daylightFraction: Double {
        guard elevation > 0 else { return 0 }
        return min(1.0, elevation / 25.0)
    }
}
