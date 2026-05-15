TRANSLATIONS = {
    "en": {
        "title": "DOCUMENT UNLOCKER PRO",
        "subtitle": "Detected Engine",
        "tabs": {
            "dashboard": " Dashboard ",
            "patterns": " Patterns ",
            "rules": " Smart Rules ",
            "dict": " Dictionary ",
            "docs": " Documentation ",
            "about": " About "
        },
        "dashboard": {
            "file_lbl": "PROTECTED DOCUMENT:",
            "browse": "Browse",
            "complexity_lbl": "ATTACK COMPLEXITY:",
            "placeholder": "Select a file to begin...",
            "boost": "SMART BOOST (Adaptive Power)",
            "boost_tip": "Prioritizes recovery processes and utilizes maximum system resources.",
            "use_dict": "USE DICTIONARY (Check common passwords first)",
            "start": "START RECOVERY",
            "smart_start": "SMART RECOVERY (Auto Chain)",
            "stop": "STOP",
            "complexities": [
                "Numeric (0-9)", 
                "Lowercase (a-z)", 
                "Uppercase (A-Z)", 
                "Alphanumeric (a-z, A-Z, 0-9)",
                "Extended (All Characters)"
            ]
        },
        "patterns": {
            "title": "CUSTOM MASK ARCHITECTURE",
            "placeholder": "e.g. Pass?d?d?d",
            "legend": "Mask Legend:",
            "digits": "Digits (0-9)",
            "lower": "Lowercase (a-z)",
            "upper": "Uppercase (A-Z)",
            "symbols": "Symbols (!@#...)",
            "all": "All characters",
            "start": "START MASK ATTACK"
        },
        "rules": {
            "lbl": "BASE KEYWORD / HINT",
            "placeholder": "Enter a known word or name...",
            "desc": "This mode uses the <b>Hybrid Rule Engine</b> to generate variations based on common password patterns (leet speak, years, capitalization).",
            "start": "START RULE ATTACK"
        },
        "dict": {
            "title": "DICTIONARY ATTACK",
            "select_lbl": "Select Wordlist:",
            "preview_lbl": "Dictionary Preview:",
            "hybrid": "HYBRID MODE (Apply Rules to Dictionary)",
            "start": "START DICTIONARY ATTACK",
            "error_dict": "Please select a dictionary file."
        },
        "status": {
            "ready": " Ready",
            "init": " Initializing hardware clusters...",
            "running": " Tested: {count} | Speed: {speed} p/s",
            "success": " Success: Password Found!",
            "failed": " Range exhausted.",
            "stopping": " Stopping clusters...",
            "error_file": "Please select a valid document first.",
            "error_mask": "Please enter a mask pattern.",
            "error_keyword": "Please enter a base keyword."
        },
        "docs_content": """
<h3>1. Smart Recovery (Recommended)</h3>
Use this for passwords like '123456'. It tries common dictionaries first, then moves to numeric brute-force.
<br><br>
<h3>2. Brute Force</h3>
Attempts every possible combination. Choose the complexity (Numeric, Alphanumeric, etc.) based on what you remember about the password.
<br><br>
<h3>3. Patterns (Mask)</h3>
If you remember parts of the password, use masks:
<ul>
  <li><b>?d</b>: Digit (0-9)</li>
  <li><b>?l</b>: Lowercase (a-z)</li>
  <li><b>?u</b>: Uppercase (A-Z)</li>
</ul>
Example: <i>Pass?d?d?d</i> will try 'Pass123', 'Pass456', etc.
<br><br>
<h3>4. Dictionary Attack</h3>
Loads a text file of passwords. Use 'Hybrid Mode' to apply rules (variations) to each word.
<br><br>
<h3>Hardware Acceleration</h3>
The app automatically detects GPUs. Use 'BOOST MODE' to maximize CPU/GPU utilization.
"""
    },
    "km": {
        "title": "កម្មវិធីដោះសោឯកសារ PRO",
        "subtitle": "ម៉ាស៊ីនដែលរកឃើញ",
        "tabs": {
            "dashboard": " ផ្ទាំងគ្រប់គ្រង ",
            "patterns": " លំនាំ ",
            "rules": " វិធានឆ្លាតវៃ ",
            "dict": " វចនានុក្រម ",
            "docs": " ឯកសារ ",
            "about": " អំពី "
        },
        "dashboard": {
            "file_lbl": "ឯកសារដែលត្រូវបានការពារ៖",
            "browse": "រុករក",
            "complexity_lbl": "កម្រិតស្មុគស្មាញនៃការវាយប្រហារ៖",
            "placeholder": "ជ្រើសរើសឯកសារដើម្បីចាប់ផ្តើម...",
            "boost": "បង្កើនល្បឿនឆ្លាតវៃ (ថាមពលសម្របតាម)",
            "boost_tip": "ផ្តល់អាទិភាពដល់ដំណើរការស្តារឡើងវិញ និងប្រើប្រាស់ធនធានប្រព័ន្ធអតិបរមា។",
            "use_dict": "ប្រើវចនានុក្រម (សាកល្បងពាក្យសម្ងាត់ទូទៅមុន)",
            "start": "ចាប់ផ្តើមការស្តារឡើងវិញ",
            "smart_start": "ការស្តារឡើងវិញដោយឆ្លាតវៃ (ស្វ័យប្រវត្តិ)",
            "stop": "បញ្ឈប់",
            "complexities": [
                "លេខ (0-9)", 
                "អក្សរតូច (a-z)", 
                "អក្សរធំ (A-Z)", 
                "អក្សរ និងលេខ (a-z, A-Z, 0-9)",
                "បន្ថែម (គ្រប់តួអក្សរ)"
            ]
        },
        "patterns": {
            "title": "ស្ថាបត្យកម្មម៉ាសប្ដូរតាមបំណង",
            "placeholder": "ឧទាហរណ៍ Pass?d?d?d",
            "legend": "ការពន្យល់អំពីម៉ាស៖",
            "digits": "លេខ (0-9)",
            "lower": "អក្សរតូច (a-z)",
            "upper": "អក្សរធំ (A-Z)",
            "symbols": "និមិត្តសញ្ញា (!@#...)",
            "all": "គ្រប់តួអក្សរទាំងអស់",
            "start": "ចាប់ផ្តើមការវាយប្រហារតាមម៉ាស"
        },
        "rules": {
            "lbl": "ពាក្យគន្លឹះមូលដ្ឋាន / តម្រុយ",
            "placeholder": "បញ្ចូលពាក្យ ឬឈ្មោះដែលស្គាល់...",
            "desc": "របៀបនេះប្រើ <b>ម៉ាស៊ីនវិធានចម្រុះ (Hybrid Rule Engine)</b> ដើម្បីបង្កើតបំរែបំរួលដោយផ្អែកលើលំនាំពាក្យសម្ងាត់ទូទៅ។",
            "start": "ចាប់ផ្តើមការវាយប្រហារតាមវិធាន"
        },
        "dict": {
            "title": "ការវាយប្រហារតាមវចនានុក្រម",
            "select_lbl": "ជ្រើសរើសបញ្ជីពាក្យ៖",
            "preview_lbl": "ការមើលបញ្ជីពាក្យជាមុន៖",
            "hybrid": "របៀបចម្រុះ (អនុវត្តវិធានចំពោះវចនានុក្រម)",
            "start": "ចាប់ផ្តើមការវាយប្រហារតាមវចនានុក្រម",
            "error_dict": "សូមជ្រើសរើសបញ្ជីពាក្យ។"
        },
        "status": {
            "ready": " រួចរាល់",
            "init": " កំពុងចាប់ផ្តើមបណ្តុំផ្នែករឹង...",
            "running": " បានសាកល្បង: {count} | ល្បឿន: {speed} p/s",
            "success": " ជោគជ័យ: រកឃើញពាក្យសម្ងាត់!",
            "failed": " បានសាកល្បងអស់ហើយ រកមិនឃើញ។",
            "stopping": " កំពុងបញ្ឈប់បណ្តុំ...",
            "error_file": "សូមជ្រើសរើសឯកសារដែលមានសុពលភាពជាមុនសិន។",
            "error_mask": "សូមបញ្ចូលលំនាំម៉ាស។",
            "error_keyword": "សូមបញ្ចូលពាក្យគន្លឹះមូលដ្ឋាន។"
        },
        "docs_content": """
<h3>១. ការស្តារឡើងវិញដោយឆ្លាតវៃ (បានណែនាំ)</h3>
ប្រើសម្រាប់ពាក្យសម្ងាត់ដូចជា '123456'។ វាសាកល្បងវចនានុក្រមទូទៅមុន បន្ទាប់មកប្តូរទៅការវាយប្រហារតាមលេខ។
<br><br>
<h3>២. ការវាយប្រហារដោយកម្លាំងបាយ (Brute Force)</h3>
សាកល្បងគ្រប់ការផ្សំទាំងអស់។ ជ្រើសរើសកម្រិតស្មុគស្មាញ (លេខ, អក្សរ និងលេខ, ។ល។) ផ្អែកលើអ្វីដែលអ្នកចងចាំ។
<br><br>
<h3>៣. លំនាំ (ម៉ាស)</h3>
ប្រសិនបើអ្នកចាំផ្នែកខ្លះនៃពាក្យសម្ងាត់ សូមប្រើម៉ាស៖
<ul>
  <li><b>?d</b>: លេខ (0-9)</li>
  <li><b>?l</b>: អក្សរតូច (a-z)</li>
  <li><b>?u</b>: អក្សរធំ (A-Z)</li>
</ul>
ឧទាហរណ៍៖ <i>Pass?d?d?d</i> នឹងសាកល្បង 'Pass123', 'Pass456', ។ល។
<br><br>
<h3>៤. ការវាយប្រហារតាមវចនានុក្រម</h3>
ផ្ទុកឯកសារអត្ថបទនៃពាក្យសម្ងាត់។ ប្រើ 'របៀបចម្រុះ' ដើម្បីអនុវត្តវិធានទៅលើពាក្យនីមួយៗ។
<br><br>
<h3>ការបង្កើនល្បឿនផ្នែករឹង</h3>
កម្មវិធីរកឃើញ GPU ដោយស្វ័យប្រវត្តិ។ ប្រើ 'របៀបបង្កើនល្បឿន' ដើម្បីប្រើប្រាស់ CPU/GPU ឱ្យអស់ពីលទ្ធភាព។
"""
    }
}

class Translator:
    def __init__(self, lang="en"):
        self.lang = lang

    def t(self, key, **kwargs):
        keys = key.split(".")
        val = TRANSLATIONS.get(self.lang, TRANSLATIONS["en"])
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, key)
            else:
                return key
        
        if isinstance(val, str):
            return val.format(**kwargs)
        return val

_instance = None

def get_translator(lang="en"):
    global _instance
    if _instance is None or _instance.lang != lang:
        _instance = Translator(lang)
    return _instance
