package com.vov.vaultopus;

import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import com.getcapacitor.BridgeActivity;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends BridgeActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Allow Mixed Content (HTTP API from HTTPS page)
        WebView webView = getBridge().getWebView();
        WebSettings settings = webView.getSettings();
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);

        // Initialize Python as early as possible
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        // Start Python Server in a background thread
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    // Small delay to let the OS network stack initialize
                    Thread.sleep(1000);
                    
                    Python py = Python.getInstance();
                    android.util.Log.i("VAULT_OPUS", "Chaquopy Ready. Importing WI.server...");
                    
                    // Import module
                    com.chaquo.python.PyObject serverModule = py.getModule("WI.server");
                    android.util.Log.i("VAULT_OPUS", "WI.server module imported successfully.");
                    
                    // Start server (blocking call)
                    android.util.Log.i("VAULT_OPUS", "Calling start_server()...");
                    serverModule.callAttr("start_server");
                    
                } catch (InterruptedException e) {
                    android.util.Log.w("VAULT_OPUS", "Python thread interrupted.");
                } catch (Exception e) {
                    android.util.Log.e("VAULT_OPUS", "FATAL Python Error: " + e.toString());
                    e.printStackTrace();
                    
                    final String errorMsg = e.toString();
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            android.widget.Toast.makeText(MainActivity.this, 
                                "Python Server Error: " + errorMsg,
                                android.widget.Toast.LENGTH_LONG).show();
                        }
                    });
                }
            }
        }).start();
    }
}
