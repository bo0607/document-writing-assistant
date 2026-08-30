# Android Mobile App

This Android Studio project wraps the document writing assistant in a mobile app.

## Build it

1. Install Android Studio with JDK 17 or newer.
2. Open `mobile/android` as an Android Studio project.
3. Let Android Studio install the Android SDK and Gradle dependencies.
4. Use **Build > Build APK(s)** to create the APK.

The phone asks for the writing service address the first time it opens. Use an HTTPS address for an internet-hosted service. For a trusted home or campus network, an address such as `http://192.168.x.x:8000` also works.

The current computer does not have a modern Android build environment, so this repository includes the full Android source project but not a generated APK.
