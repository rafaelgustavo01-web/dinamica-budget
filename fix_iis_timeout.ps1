# Fix IIS ARR responseTimeout para 10 minutos
# Execute como Administrador

$webconfig = @'
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <!-- Timeout ARR: 10min para match de PQs grandes -->
    <proxy enabled="true" reverseRewriteHostInResponseHeaders="false" responseTimeout="00:20:00" />
    <rewrite>
      <rules>
        <clear />

        <rule name="API Reverse Proxy" stopProcessing="true">
          <match url="^api/(.*)" />
          <action type="Rewrite" url="http://127.0.0.1:8000/api/{R:1}" appendQueryString="true" />
        </rule>

        <rule name="Docs Reverse Proxy" stopProcessing="true">
          <match url="^(docs|redoc|openapi\.json)$" />
          <action type="Rewrite" url="http://127.0.0.1:8000/{R:1}" appendQueryString="true" />
        </rule>

        <rule name="SPA Fallback" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>

    <staticContent>
      <remove fileExtension=".webp" />
      <mimeMap fileExtension=".webp" mimeType="image/webp" />
    </staticContent>

    <httpProtocol>
      <customHeaders>
        <add name="X-Content-Type-Options" value="nosniff" />
        <add name="Referrer-Policy" value="strict-origin-when-cross-origin" />
      </customHeaders>
    </httpProtocol>
  </system.webServer>
</configuration>
'@

Set-Content -Path "C:\inetpub\DinamicaBudget\web.config" -Value $webconfig -Encoding UTF8
Write-Host "web.config atualizado." -ForegroundColor Green

iisreset /noforce
Write-Host "IIS reiniciado." -ForegroundColor Green
