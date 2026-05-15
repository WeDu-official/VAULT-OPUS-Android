package com.vov.vaultopus;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends BridgeActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Initialize Python
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        // Start Python Server in a background thread
        new Thread(new Runnable() {
            @Override
            public void run() {
                android.util.Log.i("VAULT_OPUS", "Python Thread Started");
                try {
                    Python py = Python.getInstance();
                    android.util.Log.i("VAULT_OPUS", "Chaquopy Instance Obtained");
                    
                    // Import module to trigger top-level code
                    com.chaquo.python.PyObject serverModule = py.getModule("WI.server");
                    android.util.Log.i("VAULT_OPUS", "WI.server module imported");
                    
                    // Start server
                    serverModule.callAttr("start_server");
                    android.util.Log.i("VAULT_OPUS", "start_server() called (it may be blocking)");
                } catch (Exception e) {
                    android.util.Log.e("VAULT_OPUS", "FATAL Python Error: " + e.getMessage());
                    e.printStackTrace();
                    
                    final String errorMsg = e.getMessage();
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
