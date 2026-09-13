# Test Raporu: examples/dc3dd_suite.yaml

**Sonuç: 6/6 test başarılı**

## [PASS] dc3dd bit-bit imaj alırken kaynak dosyayla aynı hash'i üretir
- exit_code: 0

## [PASS] dc3dd üretilen hash log'unda sha256 değeri yer alır
- exit_code: 0

## [PASS] dc3dd hatalı girdi dosyasında hata verir
- exit_code: 1

## [PASS] dc3dd cnt parametresiyle sadece istenen kadar veriyi kopyalar
- exit_code: 0

## [PASS] dc3dd iskip parametresiyle doğru offsetten veriyi okur
- exit_code: 0

## [PASS] farklı tampon boyutu (bufsz=512) yine de bit-bit doğru kopya üretir
- exit_code: 0
