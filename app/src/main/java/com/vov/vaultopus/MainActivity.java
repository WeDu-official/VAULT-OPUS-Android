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
                Python py = Python.getInstance();
                // This assumes your server logic in WI/server.py 
                // is triggered upon import or has a start function
                try {
                    py.getModule("WI.server").callAttr("start_server");
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        }).start();
    }
}
