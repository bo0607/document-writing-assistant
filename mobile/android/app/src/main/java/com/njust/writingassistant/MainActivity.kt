package com.njust.writingassistant

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.webkit.DownloadListener
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    companion object {
        private const val SETTINGS_NAME = "writing_assistant_settings"
        private const val SERVER_URL_KEY = "server_url"
        private const val MENU_CHANGE_SERVER = 1
    }

    private lateinit var writingView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        supportActionBar?.title = getString(R.string.app_name)

        writingView = WebView(this)
        configureWritingView()
        setContentView(writingView)
        loadSavedServiceOrAsk()
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun configureWritingView() {
        writingView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            javaScriptCanOpenWindowsAutomatically = false
            setSupportMultipleWindows(false)
        }
        writingView.webViewClient = WebViewClient()
        writingView.webChromeClient = WebChromeClient()
        writingView.setDownloadListener(DownloadListener { url, _, _, _, _ ->
            startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        })
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menu.add(Menu.NONE, MENU_CHANGE_SERVER, Menu.NONE, R.string.change_server)
            .setShowAsAction(MenuItem.SHOW_AS_ACTION_NEVER)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        if (item.itemId == MENU_CHANGE_SERVER) {
            askForServiceAddress()
            return true
        }
        return super.onOptionsItemSelected(item)
    }

    private fun loadSavedServiceOrAsk() {
        val savedUrl = settings().getString(SERVER_URL_KEY, "").orEmpty()
        if (savedUrl.isBlank()) {
            askForServiceAddress(firstUse = true)
        } else {
            writingView.loadUrl(savedUrl)
        }
    }

    private fun askForServiceAddress(firstUse: Boolean = false) {
        val input = EditText(this).apply {
            hint = getString(R.string.server_hint)
            setText(settings().getString(SERVER_URL_KEY, ""))
            selectAll()
            setSingleLine(true)
        }

        AlertDialog.Builder(this)
            .setTitle(R.string.server_title)
            .setMessage(R.string.server_message)
            .setView(input)
            .setPositiveButton(R.string.connect) { _, _ ->
                val address = normalizeAddress(input.text.toString())
                if (address == null) {
                    Toast.makeText(this, R.string.server_invalid, Toast.LENGTH_LONG).show()
                    askForServiceAddress(firstUse)
                    return@setPositiveButton
                }
                settings().edit().putString(SERVER_URL_KEY, address).apply()
                writingView.loadUrl(address)
            }
            .setNegativeButton(if (firstUse) R.string.exit else android.R.string.cancel) { _, _ ->
                if (firstUse) finish()
            }
            .show()
    }

    private fun normalizeAddress(value: String): String? {
        val candidate = value.trim().removeSuffix("/").let {
            if (it.startsWith("http://") || it.startsWith("https://")) it else "http://$it"
        }
        val uri = Uri.parse(candidate)
        return if ((uri.scheme == "http" || uri.scheme == "https") && !uri.host.isNullOrBlank()) {
            candidate
        } else {
            null
        }
    }

    private fun settings() = getSharedPreferences(SETTINGS_NAME, Context.MODE_PRIVATE)

    @Deprecated("Use OnBackPressedDispatcher for new code")
    override fun onBackPressed() {
        if (writingView.canGoBack()) {
            writingView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
