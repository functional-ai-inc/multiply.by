import java.util.Properties
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// Release signing: the upload key (never in git; see ANDROID.md, "Release build"), from
// android/upload-key.properties or else ~/.multiply-play/upload-key.properties (the owner's copy,
// read in place: nothing to copy before a build). Its storeFile is relative to the properties
// file's folder. Without either, a release build stops (end of this file).
val keyFile: File = listOf(
    rootProject.file("upload-key.properties"),
    File(System.getProperty("user.home"), ".multiply-play/upload-key.properties"),
).firstOrNull { it.exists() } ?: rootProject.file("upload-key.properties")

android {
    namespace = "by.multiply.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "by.multiply.app"   // never change after publishing
        minSdk = 24
        targetSdk = 36
        versionCode = 3        // +1 for every upload to Play
        versionName = "1.0"
    }

    // Release signing with the upload key (keyFile, above).
    if (keyFile.exists()) {
        val key = Properties().apply { keyFile.inputStream().use { load(it) } }
        signingConfigs {
            create("upload") {
                val store = File(key.getProperty("storeFile"))
                storeFile = if (store.isAbsolute) store else File(keyFile.parentFile, store.path)
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

// A release build without the upload key would be unsigned, and Play refuses it: stop instead.
gradle.taskGraph.whenReady {
    val release = allTasks.any {
        it.project == project && it.name.endsWith("Release") &&
            (it.name.startsWith("bundle") || it.name.startsWith("assemble"))
    }
    if (release && !keyFile.exists()) {
        throw GradleException(
            "No upload key: put upload-key.properties and upload-key.jks in ~/.multiply-play/ " +
            "(or in the android folder). See ANDROID.md, \"Release build\".")
    }
}
