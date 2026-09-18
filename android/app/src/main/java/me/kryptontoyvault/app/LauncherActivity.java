package me.kryptontoyvault.app;

import android.content.pm.ActivityInfo;
import android.os.Build;
import android.os.Bundle;

/**
 * Trusted Web Activity launcher for https://kryptons-toy-vault.grok.me
 */
public class LauncherActivity extends com.google.androidbrowserhelper.trusted.LauncherActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Transparent splash + orientation crashes on Android 8.0; skip there.
        // https://github.com/GoogleChromeLabs/bubblewrap/issues/496
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.O) {
            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED);
        }
    }
}
