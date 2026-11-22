import java.util.Properties
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "by.multiply.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "by.multiply.app"   // never change after publishing
        minSdk = 24
        targetSdk = 36
        versionCode = 1        // +1 for every upload to Play
        versionName = "1.0"
    }

    // Release signing: the upload key, from android/upload-key.properties (never in git; see
    // ANDROID.md, "Release build"). Without that file a release build is left unsigned.
    val keyFile = rootProject.file("upload-key.properties")
    if (keyFile.exists()) {
        val key = Properties().apply { keyFile.inputStream().use { load(it) } }
        signingConfigs {
            create("upload") {
                storeFile = rootProject.file(key.getProperty("storeFile"))
                storePassword = key.getProperty("storePassword")
                keyAlias = key.getProperty("keyAlias")
                keyPassword = key.getProperty("keyPassword")
            }
        }
    }

    buildFeatures { buildConfig = true }

    buildTypes {
        release {
            if (keyFile.exists()) signingConfig = signingConfigs.getByName("upload")
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

dependencies {
    implementation("androidx.activity:activity-ktx:1.10.1")
    implementation("androidx.webkit:webkit:1.14.0")
}

// The pages come from gather-assets.py (they are not in the repo): stop with a clear message.
val siteFiles = layout.projectDirectory.file("src/main/assets/site/files.txt")
tasks.named("preBuild") {
    doFirst {
        if (!siteFiles.asFile.exists()) {
            throw GradleException(
                "The games are missing: run  python3 gather-assets.py  in the android folder first.")
        }
    }
}
