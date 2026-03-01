# ============================================
# SimuTarget - Görsel Upload Özelliği Test Scripti
# ============================================

$BASE_URL = "http://localhost:8000/api/v1"

# ---- 1. Giriş Yap ----
Write-Host "`n=== 1. Login ===" -ForegroundColor Cyan

$loginBody = @{
    username = "test@test.com"
    password = "test123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Method POST `
        -Uri "$BASE_URL/auth/login" `
        -ContentType "application/json" `
        -Body $loginBody
    
    $TOKEN = $loginResponse.access_token
    Write-Host "Token alindi: $($TOKEN.Substring(0,20))..." -ForegroundColor Green
}
catch {
    Write-Host "Login hatasi: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

$headers = @{
    "Authorization" = "Bearer $TOKEN"
}

# ---- 2. Kampanya Oluştur ----
Write-Host "`n=== 2. Kampanya Olustur ===" -ForegroundColor Cyan
$campaignBody = @{
    name = "Gorsel Test Kampanyasi"
    content = "Yeni urunumuz cok ozel! Simdi yuzde 30 indirimle satin alin."
    region = "TR"
} | ConvertTo-Json

try {
    $campaign = Invoke-RestMethod -Method POST `
        -Uri "$BASE_URL/campaigns/" `
        -ContentType "application/json" `
        -Headers $headers `
        -Body $campaignBody

    $CAMPAIGN_ID = $campaign.id
    Write-Host "Kampanya olusturuldu: ID=$CAMPAIGN_ID" -ForegroundColor Green
    Write-Host "has_image: $($campaign.has_image)" -ForegroundColor Yellow
}
catch {
    Write-Host "Kampanya hatasi: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

# ---- 3. Görsel Yükle ----
Write-Host "`n=== 3. Gorsel Yukle ===" -ForegroundColor Cyan

$testImagePath = "$env:TEMP\test_campaign_image.png"
$pngBytes = [byte[]]@(
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
    0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
    0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
    0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
    0x44, 0xAE, 0x42, 0x60, 0x82
)
[System.IO.File]::WriteAllBytes($testImagePath, $pngBytes)
Write-Host "Test gorseli olusturuldu: $testImagePath"

try {
    $boundary = [System.Guid]::NewGuid().ToString()
    $fileBytes = [System.IO.File]::ReadAllBytes($testImagePath)
    $fileEnc = [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileBytes)
    
    $LF = "`r`n"
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"test_image.png`"",
        "Content-Type: image/png$LF",
        $fileEnc,
        "--$boundary--$LF"
    ) -join $LF

    $uploadResponse = Invoke-RestMethod -Method POST `
        -Uri "$BASE_URL/campaigns/$CAMPAIGN_ID/upload-image" `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Headers $headers `
        -Body $bodyLines
    
    Write-Host "Gorsel yuklendi!" -ForegroundColor Green
    Write-Host "  Dosya: $($uploadResponse.image_filename)"
    Write-Host "  Boyut: $($uploadResponse.image_size_kb) KB"
    Write-Host "  Tip: $($uploadResponse.content_type)"
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.Value__
    Write-Host "Gorsel yukleme hatasi: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status: $statusCode" -ForegroundColor Red
    
    if ($statusCode -eq 403) {
        Write-Host ">>> Kullanicinin plani gorsel desteklemiyor. Pro veya ustu plan gerekli." -ForegroundColor Yellow
    }
}

# ---- 4. Kampanya Detay Kontrol ----
Write-Host "`n=== 4. Kampanya Detay Kontrol ===" -ForegroundColor Cyan
try {
    $campaignDetail = Invoke-RestMethod -Method GET `
        -Uri "$BASE_URL/campaigns/$CAMPAIGN_ID" `
        -Headers $headers

    Write-Host "has_image: $($campaignDetail.has_image)" -ForegroundColor Yellow
    Write-Host "image_filename: $($campaignDetail.image_filename)" -ForegroundColor Yellow
}
catch {
    Write-Host "Detay hatasi: $($_.Exception.Message)" -ForegroundColor Red
}

# ---- 5. Görsel ile Test ----
Write-Host "`n=== 5. Gorsel Kampanya Testi ===" -ForegroundColor Cyan
$testBody = @{
    persona_count = 3
    region = "TR"
    lang = "tr"
} | ConvertTo-Json

try {
    $testResult = Invoke-RestMethod -Method POST `
        -Uri "$BASE_URL/campaigns/$CAMPAIGN_ID/test" `
        -ContentType "application/json" `
        -Headers $headers `
        -Body $testBody
    
    Write-Host "Test tamamlandi!" -ForegroundColor Green
    Write-Host "  Toplam: $($testResult.total_personas)"
    Write-Host "  Evet: $($testResult.yes_count)"
    Write-Host "  Hayir: $($testResult.no_count)"
    Write-Host "  Conversion: $($testResult.conversion_rate)%"
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.Value__
    Write-Host "Test hatasi ($statusCode): $($_.Exception.Message)" -ForegroundColor Red
}

# ---- 6. Görseli Sil ----
Write-Host "`n=== 6. Gorsel Sil ===" -ForegroundColor Cyan
try {
    $deleteResult = Invoke-RestMethod -Method DELETE `
        -Uri "$BASE_URL/campaigns/$CAMPAIGN_ID/image" `
        -Headers $headers
    
    Write-Host "Gorsel silindi: $($deleteResult.message)" -ForegroundColor Green
}
catch {
    Write-Host "Silme hatasi: $($_.Exception.Message)" -ForegroundColor Red
}

# Temizlik
if (Test-Path $testImagePath) { Remove-Item $testImagePath }

Write-Host "`n=== TEST TAMAMLANDI ===" -ForegroundColor Cyan