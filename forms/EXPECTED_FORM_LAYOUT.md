# Guj Premium Video form v2.1 - expected layout (after upgradeV2)

21 sections. Every title must match exactly. "-> X" = go to section X for that answer.
"[previous section exits to: X]" = the section before this one continues to X.

```text
[1] (first section - ઉમેદવાર)
   Multiple choice ઉમેદવાર (Candidate)  *required
        • છોકરો (Boy)
        • છોકરી (Girl)
   Short answer    ઉમેદવારનું પૂરું નામ - ગુજરાતીમાં (Full name)  *required
   Short answer    પહેલું નામ - ગુજરાતીમાં (First name)  *required
   Short answer    ગામ (Native village)  *required
   Short answer    હાલ (Current city / area)  *required
   Dropdown        જન્મ વર્ષ (Birth year)  *required
        • 2008 … 1965  (44 options)
   Multiple choice વૈવાહિક સ્થિતિ (Marital status)  *required
        • Single
        • Divorced
        • Widow
        • Widower
   Dropdown        ઊંચાઈ (Height)  *required
        • 4'6" … 6'6"  (25 options)
   Short answer    સમાજ / ફિરકો (e.g. દેરાવાસી જૈન)  *required
   Short answer    શોખ - English, comma separated (Hobbies)
   Short answer    CommuTree profile link
   Multiple choice ઉમેદવારના ફોટા વિડિયોમાં (Candidate photos in video)  *required
        • Show clearly
        • Blur
        • Hide (no candidate photos)
   File upload     ફોટો: ઉમેદવાર - મુખ્ય ફોટો (Main photo)  *required
   File upload     ફોટા: ઉમેદવાર - ગેલેરી, 6 to 10 photos (Gallery)

[2] દાદા-દાદી
   Short answer    દાદા-દાદી - નામ (e.g. દાદીનું નામ + દાદાનું નામ + અટક)
   Short answer    દાદા-દાદી - ગામ
   File upload     ફોટો: દાદી
   File upload     ફોટો: દાદા
   File upload     ફોટો: દાદા-દાદી સાથે (couple photo, optional)

[3] નાના-નાની
   Short answer    નાના-નાની - નામ (e.g. નાનીનું નામ + નાનાનું નામ + અટક)
   Short answer    નાના-નાની - ગામ
   File upload     ફોટો: નાની
   File upload     ફોટો: નાના
   File upload     ફોટો: નાના-નાની સાથે (couple photo, optional)

[4] માતા-પિતા
   Short answer    માતા-પિતા - નામ (માતાનું પૂરું નામ, e.g. દિવ્યા નિલેશ ખિમજી મારૂ)
   Short answer    માતા-પિતા - ગામ
   Short answer    માતા-પિતા - હાલ
   Short answer    માતાનું ટૂંકું નામ (e.g. દિવ્યાબેન)
   Paragraph       માતાનો વ્યવસાય - one line per row (e.g. HouseWife)
   Short answer    પિતાનું ટૂંકું નામ (e.g. નિલેશભાઈ)
   Paragraph       પિતાનો વ્યવસાય - one line per row (e.g. Business: / Company, City / (Description))
   File upload     ફોટો: માતા
   File upload     ફોટો: પિતા
   File upload     ફોટો: માતા-પિતા સાથે (couple photo, optional)

[5] ભાઈ/બહેન 1
   Multiple choice ભાઈ/બહેન 1 - સંબંધ (Sibling 1)  *required
        • બહેન - બનેવી  -> ભાઈ/બહેન 1 - બહેન-બનેવી વિગત
        • ભાઈ - ભાભી  -> ભાઈ/બહેન 1 - ભાઈ-ભાભી વિગત
        • મોટા ભાઈ - ભાભી  -> ભાઈ/બહેન 1 - ભાઈ-ભાભી વિગત
        • ભાઈ (અપરિણીત)  -> ભાઈ/બહેન 1 - ભાઈ વિગત
        • બહેન (અપરિણીત)  -> ભાઈ/બહેન 1 - બહેન વિગત
        • કોઈ નહીં / વધુ નથી (None)  -> અભ્યાસ

[6] ભાઈ/બહેન 1 - બહેન-બનેવી વિગત
   Short answer    બહેનનું નામ (first name, e.g. કિંજલ)
   Short answer    બનેવીનું પૂરું નામ (e.g. દિવ્ય ભાવેશ રાંભિયા)
   Short answer    બહેન-બનેવી હાલ (place)
   Short answer    બહેનનો વ્યવસાય / અભ્યાસ
   Short answer    બનેવીનો વ્યવસાય

[7] ભાઈ/બહેન 1 - ભાઈ-ભાભી વિગત   [previous section exits to: ભાઈ/બહેન 1 - ફોટો]
   Short answer    ભાઈનું પૂરું નામ (e.g. હાર્દિક મનોજ મારૂ)
   Short answer    ભાભીનું નામ (first name)
   Short answer    ભાઈ-ભાભી હાલ (place)
   Short answer    ભાઈનો વ્યવસાય
   Short answer    ભાભીનો વ્યવસાય / અભ્યાસ

[8] ભાઈ/બહેન 1 - ભાઈ વિગત   [previous section exits to: ભાઈ/બહેન 1 - ફોટો]
   Short answer    ભાઈનું પૂરું નામ (unmarried)
   Short answer    ભાઈ હાલ (place)
   Short answer    ભાઈનો અભ્યાસ / વ્યવસાય (e.g. STUDENT)

[9] ભાઈ/બહેન 1 - બહેન વિગત   [previous section exits to: ભાઈ/બહેન 1 - ફોટો]
   Short answer    બહેનનું પૂરું નામ (unmarried)
   Short answer    બહેન હાલ (place)
   Short answer    બહેનનો અભ્યાસ / વ્યવસાય

[10] ભાઈ/બહેન 1 - ફોટો
   File upload     ફોટો: ભાઈ/બહેન 1 (1 couple photo or 2 separate)
   Multiple choice ભાઈ/બહેન 2 - સંબંધ (Sibling 2)  *required
        • બહેન - બનેવી  -> ભાઈ/બહેન 2 - બહેન-બનેવી વિગત
        • ભાઈ - ભાભી  -> ભાઈ/બહેન 2 - ભાઈ-ભાભી વિગત
        • મોટા ભાઈ - ભાભી  -> ભાઈ/બહેન 2 - ભાઈ-ભાભી વિગત
        • ભાઈ (અપરિણીત)  -> ભાઈ/બહેન 2 - ભાઈ વિગત
        • બહેન (અપરિણીત)  -> ભાઈ/બહેન 2 - બહેન વિગત
        • કોઈ નહીં / વધુ નથી (None)  -> અભ્યાસ

[11] ભાઈ/બહેન 2 - બહેન-બનેવી વિગત
   Short answer    બહેનનું નામ (first name, e.g. કિંજલ)
   Short answer    બનેવીનું પૂરું નામ (e.g. દિવ્ય ભાવેશ રાંભિયા)
   Short answer    બહેન-બનેવી હાલ (place)
   Short answer    બહેનનો વ્યવસાય / અભ્યાસ
   Short answer    બનેવીનો વ્યવસાય

[12] ભાઈ/બહેન 2 - ભાઈ-ભાભી વિગત   [previous section exits to: ભાઈ/બહેન 2 - ફોટો]
   Short answer    ભાઈનું પૂરું નામ (e.g. હાર્દિક મનોજ મારૂ)
   Short answer    ભાભીનું નામ (first name)
   Short answer    ભાઈ-ભાભી હાલ (place)
   Short answer    ભાઈનો વ્યવસાય
   Short answer    ભાભીનો વ્યવસાય / અભ્યાસ

[13] ભાઈ/બહેન 2 - ભાઈ વિગત   [previous section exits to: ભાઈ/બહેન 2 - ફોટો]
   Short answer    ભાઈનું પૂરું નામ (unmarried)
   Short answer    ભાઈ હાલ (place)
   Short answer    ભાઈનો અભ્યાસ / વ્યવસાય (e.g. STUDENT)

[14] ભાઈ/બહેન 2 - બહેન વિગત   [previous section exits to: ભાઈ/બહેન 2 - ફોટો]
   Short answer    બહેનનું પૂરું નામ (unmarried)
   Short answer    બહેન હાલ (place)
   Short answer    બહેનનો અભ્યાસ / વ્યવસાય

[15] ભાઈ/બહેન 2 - ફોટો
   File upload     ફોટો: ભાઈ/બહેન 2 (1 couple photo or 2 separate)

[16] અભ્યાસ
   Short answer    અભ્યાસ 1 - Degree (e.g. B.Com)
   Short answer    અભ્યાસ 1 - College / University
   Short answer    અભ્યાસ 2 - Degree (optional)
   Short answer    અભ્યાસ 2 - College / University (optional)
   File upload     ફોટો: અભ્યાસ કાર્ડ માટે (optional)

[17] વ્યવસાય
   Multiple choice વ્યવસાય પ્રકાર (Occupation type)  *required
        • ફેમિલી બિઝનેસ (Family Business)  -> વ્યવસાય - બિઝનેસ વિગત
        • પોતાનો બિઝનેસ (Own Business)  -> વ્યવસાય - બિઝનેસ વિગત
        • નોકરી (Job)  -> વ્યવસાય - નોકરી / પ્રોફેશન વિગત
        • પ્રોફેશનલ / સ્વરોજગાર (Professional / Self-employed)  -> વ્યવસાય - નોકરી / પ્રોફેશન વિગત
        • કોઈ નહીં / અભ્યાસ ચાલુ (None / Studying)  -> Income / Property

[18] વ્યવસાય - બિઝનેસ વિગત
   Short answer    કંપની / બિઝનેસ નામ, શહેર (e.g. Maru nx, Dombivali)
   Short answer    બિઝનેસ / કામ વિશે (e.g. Retailer of Steel & Home Appliances)

[19] વ્યવસાય - નોકરી / પ્રોફેશન વિગત   [previous section exits to: વ્યવસાય - ફોટો / લોગો]
   Paragraph       નોકરી / પ્રોફેશન - points, one per line (e.g. Manager at ABC Ltd, Mumbai)

[20] વ્યવસાય - ફોટો / લોગો
   File upload     ફોટો: વ્યવસાય કાર્ડ માટે (optional)
   File upload     લોગો: કંપની / બિઝનેસ (PNG, optional)

[21] Income / Property
   Short answer    Income (optional, e.g. 20-50 Lakhs p.a.)
   Paragraph       Property - one per line (e.g. Residence 3BHK at Mulund)
```
