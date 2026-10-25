# Audit senior AI engineering: peluang peningkatan skor

Tanggal: 25 Oktober 2026. Analisis implementasi dan laporan lokal, bukan perubahan solver atau eksperimen model baru. Tidak ada jaminan skor sempurna: bobot grader tersembunyi dan delapan verdict belum dapat dibuktikan dengan evidence yang tersedia.

## Dasar dan hasil yang benar-benar tersedia

Sumber utama: problem_statement.md; AGENTS.md bagian 6; seluruh 15 baris dataset/deletion_rules.csv; code/deletion_audit/{authorization,state,policy,planner,evaluator,agent_context,ai_auditor,investigator}.py; docs/{agent_capabilities,final_forensic_review,submission_recovery}.md; artifacts/agent_capabilities/{summary,verification}.json; artifacts/submission_recovery/sample_mismatches.json. Temuan trace historis diperiksa melalui laporan audit dan replay yang tersedia, bukan eksekusi ulang API pada audit ini.

| Ukuran | Hasil terakhir yang direkam |
| --- | ---: |
| Status sample | 29/32 = 90.625% |
| Exact case / sequence sample | 9/32 = 28.125% |
| Step precision / recall | 97.546012% / 82.383420% |
| Step F1 / field accuracy | 89.325843% / 77.447426% |
| Sample lolos kontrak | 29/32 |
| Full lolos kontrak | 510/518 |
| Full lolos verdict dan kelengkapan proof/plan internal | 509/518 |
| Test terakhir, working dan extracted source | 273 lulus |
| Replay proposal historis | 4 duplicate, 5 rejected, 0 perubahan prediction |
| Kenaikan akurasi sample yang terbukti berasal dari AI | Belum ada |

Angka di atas dibaca ulang dari artifact; suite dan model tidak dijalankan ulang dalam audit ini. Source ZIP terakhir berisi 77 file dan lulus pemeriksaan Windows, bukan bukti OCR native lintas OS. Root output.csv dan candidate tetap belum diterbitkan. Validasi kontrak bukan sertifikat bahwa seluruh klaim semantik benar.

## Tuntutan lomba versus kelengkapan aktual

Problem statement menyatakan: "Scoring will consider the correctness of deletion_status, identity resolution, discovered records and risks, cited evidence, policy decisions, and the completeness and order of steps_json." Tidak ada bobot numerik yang tersedia dalam statement lokal; prioritas berikut berdasarkan error aktual, bukan dugaan bobot grader.

| Aspek wajib | Yang sudah ada | Kekurangan / tindakan bernilai |
| --- | --- | --- |
| Otorisasi deletion multilingual | Gate deterministik dan pemisahan NOT_APPLICABLE | Negasi perlu mengikuti objek dan klausa; contoh gagal terbukti di bawah |
| Current/historical identity | Graph, hash, resource links, cutoff | Identitas request terjawab tidak berarti semua resource terhubung; historical ownership untuk data anonymized masih bottleneck |
| Semua bukti dan multimodal | Manifest, provenance, parser, 11 PNG OCR, vision opsional | File berhasil dibaca tidak berarti setiap fakta atau scope berhasil diekstrak |
| Rekonstruksi audit_at | Capture/event time, replica, kontradiksi, scoped negatives | Audit entailment setiap compliant-state proof; jangan anggap null parsial sebagai redaksi lengkap |
| Semua 15 policy | Rule-driven decisions dan conditional guards | Kondisi harus dibuktikan per resource; keberadaan kategori saja bukan bukti semua kondisi berlaku |
| Remediation dan verification lengkap | Planner canonical, future evidence_id kosong | 34 verification reference belum tercakup; banyak merupakan ownership gap sebelum planner |
| AI-powered investigation | Single agent, lima tools read-only, grounding, cache, batas biaya | Kemampuan mekanis sudah ada; belum ada bukti incremental accuracy di corpus nyata |
| Output 518 baris sah | Diagnostic full berisi 518 baris | Delapan status kosong tidak sesuai kontrak; satu plan tambahan belum lengkap |
| Evaluasi dan custom cases | Evaluator, laporan, custom fixtures, regresi | Butuh evaluasi kontribusi AI dan error semantic di luar jumlah tests |
| Packaging dan usage | ZIP tervalidasi, README, required reports, secret exclusions | Final-run usage belum bisa disebut run penghasil output.csv; native trace ZIP menunggu sesi ditutup |

## Error sample: fokus pada penyebab, bukan gejala

Ada 159 step cocok dari 193 reference, 34 missing dan 4 extra. Semua 34 missing merupakan verification. Pengelompokan diagnostik:

| Penyebab missing step | Jumlah step | Makna implementasi |
| --- | ---: | --- |
| Belum ada grounded subject link di parsed evidence | 17 | Cari relasi literal di original source; belum berarti relasi memang tersedia |
| Link hanya tersedia setelah cutoff | 8 | Bukan permission untuk backfill; model tidak boleh memperbaikinya dengan menebak |
| Anonymized record tanpa historical resource link | 7 | Cari ownership sebelum anonymization, bukan identifier yang sudah dihapus |
| Retained record tanpa admissible subject link | 2 | Cari stable reference / FK dengan capture dan event time yang sah |

Terdapat 45 perbedaan step_no pada anchor yang cocok, tanpa perbedaan field/citation lain pada anchor tersebut. Karena numbering bergeser saat step hilang/bertambah, memperbaiki numbering sendiri tidak menyelesaikan penyebabnya. Evidence pada missing/extra steps tetap perlu diaudit terpisah; hasil anchored comparison tidak membuktikan semua citation lengkap.

Tiga extra steps berasal dari object_19: temuan, delete, verification. Review sebelumnya menemukan literal catalog ownership dan listing presence yang mendukungnya. Menghapus langkah tersebut hanya agar reference cocok tidak dibenarkan. Persistensi state dari positive readback lama tetap merupakan asumsi temporal yang harus dijelaskan dan diuji konsisten, bukan fresh readback baru.

## Dua celah correctness yang direproduksi pada audit ini

### A. Negasi multilingual tidak mengikat objek

Eksekusi langsung authorize() menghasilkan:

| Input fixture independen | Hasil saat ini | Interpretasi yang semestinya |
| --- | --- | --- |
| Quiero eliminar mi cuenta. No borres mis facturas. | authorized=false | Menghapus akun; mempertahankan faktur |
| Hapus akun saya. Jangan hapus faktur yang wajib disimpan. | authorized=false | Menghapus akun; mempertahankan faktur |
| Please delete my account. Do not delete invoices that must be retained. | authorized=true | Menghapus akun; mempertahankan faktur |

authorization.py menggunakan negative regex seluruh request, lalu pengecualian explicit account deletion hanya dalam bentuk Inggris tertentu. Ini cacat generalisasi yang nyata, tetapi belum dibuktikan menyebabkan salah satu prediction sample/full aktual. Perbaikan: ekstraksi intent per klausa, target akun/data versus dokumen yang dipertahankan, dan negasi lokal. Gunakan fallback AI hanya untuk UNKNOWN dengan output intent terstruktur dan span kutipan; consent tidak boleh ditentukan dari reported_status. Uji negasi, koordinasi klausa, koreksi, opt-out, audit-only dan tiap bahasa yang benar-benar ada di dataset.

### B. Helper state menerima null parsial sebagai tidak exposed

Eksekusi exposed({'email': None}) dan exposed({'email': None}, anonymize=True) sama-sama mengembalikan false. observed_state() menggunakan hasil ini untuk kategori redaction/anonymization. Secara semantik, email kosong saja tidak membuktikan name/phone/hash atau stable user link sudah dihapus. Jalur EXTRACT_FIELDS baru sudah mewajibkan cakupan lebih lengkap, tetapi helper umum tetap menerima pola ini pada jalur lama.

Perbaikan bernilai adalah audit sumber dan field coverage sebelum mengubah perilaku: bedakan field tidak diekspor, field benar-benar null, redaction certificate eksplisit, dan complete row schema. State tanpa cakupan cukup harus UNKNOWN, bukan REDACTED/ANONYMIZED. Untuk anonymization, hilangnya direct PII belum cukup bila stable subject link masih ada. Belum diukur apakah pola helper ini menghasilkan false COMPLETE pada corpus aktual; perubahan konservatif juga dapat menurunkan coverage, jadi jangan menjualnya sebagai kenaikan skor yang sudah pasti.

## Agent: apa yang masih kurang dan perbaikan paling kecil

1. **Hentikan draft berdasarkan kebutuhan bukti, bukan posisi turn saja.** _loop() meminta draft pada turn kedua bila tool sebelumnya tidak error/paginated. Hasil lengkap dapat tetap memperkenalkan filename/resource/FK baru yang membutuhkan tool lanjutan. Saat itu agent hanya mendapat satu putaran retrieval sebelum draft dan correction. Keberadaan paging bukan ukuran cukupnya investigasi. Gunakan proof-goal completion dan unresolved follow-up leads untuk memilih retrieval atau draft, tetap maksimum tiga model turns dan enam successful tools. Ini hipotesis perbaikan workflow dari kode, belum live-proven.
2. **Pilih target berdasarkan peluang proof delta.** Prioritaskan raw source dengan exact subject/FK, field yang belum typed, atau temporal join yang bisa diverifikasi. Jangan membayar ulang untuk kasus tanpa data, post-cutoff-only, dan konflik identitas yang sudah terbukti. source_leads saat ini sudah ada; yang kurang adalah ranking dan measured yield per jenis goal, bukan menambah retrieval framework.
3. **Uji validator false rejection secara terkontrol.** EXTRACT_FIELDS membatasi canonical keys, marker direct_readback/snapshot_row, dan structured bindings. Ini proteksi baik, tetapi bisa melewatkan makna asli PDF/text atau alias field yang sah. Audit rejected proposals terhadap source secara offline. Tambah adapter alias hanya jika semantik dan scope dibuktikan, jangan longgarkan semua checks atau menganggap hasil LLM sebagai evidence.
4. **Pisahkan reasoning claim dari fact extraction.** Agen boleh menyarankan makna condition, resource relation dan konflik; deterministic layer tetap menetapkan policy/verdict. Usulan harus menyebut original span/pointer, waktu, subject/resource, dan batas scope. Ownership link tidak otomatis membuktikan current state.
5. **Vision berdasarkan missing visible fact, bukan sekadar ada PNG.** OCR semua gambar sudah tersedia. Vision berguna hanya bila layout/label yang terlihat dapat menyelesaikan proof goal dan belum tercakup OCR. Screenshot yang menampilkan orang berbeda tidak dapat dipakai untuk memperbaiki ownership katalog dengan voting model.
6. **Buktikan kontribusi end-to-end.** Jalur LINK_IDENTITY/EXTRACT_FIELDS terbaru sudah lolos mock/unit tests, tetapi prompt/tools baru belum diuji live. Replay final proposal lama hanya menguji validator baru; replay tidak dapat membuktikan agent baru akan memilih tools lebih baik. Tidak perlu paid batch sekarang: inventaris lead baru yang admissible dulu. Pilot baru hanya layak jika ada source baru yang berpotensi menambah proof; hentikan bila hanya duplicate/rejection.

Truncation, schema resource/system_id, category enum, bounded grounding correction, provenance dan metadata handoff sudah diperbaiki. Menawarkannya lagi sebagai pekerjaan baru tidak menambah skor. Multi-agent, vector DB, model lebih mahal dan budget lebih besar tidak mempunyai dasar manfaat pada hasil saat ini.

## Workflow evaluasi yang perlu dipertajam

- Gunakan rantai ukur: available lead -> retrieved source -> valid relation/field -> unique fact -> completed obligation -> output delta -> reference delta. Accepted proposal count sendiri adalah vanity metric bila semua duplicate.
- Laporkan precision/recall per kategori, phase, source family dan jenis failure; 97.55% micro precision dapat menutupi resource yang tidak ditemukan.
- Pertahankan dua evaluasi terpisah: reference agreement dan source/policy correctness. Discrepancy reference bukan alasan mengubah fakta. Strict validator saat ini memeriksa schema/citation chronology; evaluasi semantik perlu proof checks tambahan.
- Tambahkan pasangan counterfactual independen: satu field PII tersisa, replica kotor, ownership berubah, snapshot partial versus exhaustive, timestamp tepat cutoff, dan permission backup tidak ditampilkan. Ukur false COMPLETE dan false NOT_APPLICABLE, bukan hanya jumlah tests lulus.
- Pisahkan kategori blocker irreducible dari parser/join bug yang bisa ditindak. Hindari terus menjalankan model untuk delapan kasus yang sudah tidak memiliki bukti penentu.
- Ukur token dan biaya per novel fact, per resolved obligation, serta per corrected case. Pertahankan paired baseline/agent dengan sumber, cutoff dan dataset hash identik. Jangan memilih hanya kasus yang berhasil untuk klaim agregat.

## Prioritas implementasi dan syarat keberhasilan

| Urutan | Pekerjaan | Dampak yang diharapkan | Syarat penerimaan |
| --- | --- | --- | --- |
| P0 | Audit source-to-obligation untuk 34 missing verification | Peluang langsung meningkatkan recall/exact terbesar; sebagian mungkin tidak dapat diperbaiki | Ada admissible ownership + state proof, tidak ada sample ID/label dalam prediction |
| P0 | Field-coverage audit pada jalur state lama | Mengurangi false COMPLETE; kenaikan skor belum terbukti | Tidak lagi menyimpulkan clean dari omitted fields, regresi dan delta corpus dilaporkan |
| P1 | Intent negation per klausa dan objek multilingual | Mengurangi false NOT_APPLICABLE | Fixture lintas bahasa lulus; corpus dinilai ulang tanpa hardcode |
| P1 | Retrieval/draft berbasis proof goals dengan budget tetap | Memungkinkan investigation adaptif kedua saat berguna | Independent two-hop fixture; tidak ada turn/call/cost tambahan |
| P1 | Audit novelty dan rejected-proof coverage | Mengidentifikasi adapter general yang benar-benar berguna | Source-backed new facts dan prediction delta, bukan ID baru semata |
| P2 | Evaluasi terstratifikasi + ablation deterministik/AI | Memperjelas investasi yang layak | Semua sample dilaporkan; biaya dan regresi terlihat |
| P0 submission | Freeze artifact, trace akhir, laporan final run yang jujur | Mencegah gagal deliverable | Tidak menamai diagnostic sebagai fully valid output; semua artifact nyata |

Masing-masing perubahan dijalankan satu per satu dengan same-input baseline. Jangan menggabungkan beberapa hipotesis lalu mengatribusikan delta kepada model. Bila precision turun, periksa validitas langkah baru terhadap policy dan sumber sebelum memutuskan berdasarkan reference score.

## Batas yang tidak bisa diselesaikan oleh agent lebih pintar

Delapan verdict belum terselesaikan: case_46 (tombstone fields), case_55 (archive restore permissions), case_63 (konflik screenshot/catalog identity), case_506/case_512/case_524/case_530/case_532 (primary-account/coverage proof yang tidak memadai). case_34 sudah INCOMPLETE karena pelanggaran lain, tetapi retention condition audit record belum diketahui. Detail per sumber dan cutoff ada dalam docs/final_forensic_review.md.

Statement: "For COMPLETE, include only verification steps proving the current state." Untuk INCOMPLETE, statement mewajibkan findings dan complete remediation plan. Tidak ada definisi eksplisit yang menyamakan kegagalan membuktikan COMPLETE dengan bukti INCOMPLETE. Tanpa data penentu, memaksa salah satu status memerlukan asumsi tambahan dan tidak dapat disebut evidence-validated. Tidak ada permitted restoration operation untuk menutup missing retained record secara spekulatif.

Karena panitia tidak dapat ditanya, perlakukan ini sebagai batas yang diketahui, bukan dependency workflow. Maksimalkan kasus yang dapat dibuktikan dan jelaskan incompatibility mandatory-three-status versus insufficient evidence. Nilai sempurna dan output 518/518 yang benar belum bisa dijanjikan. Menyembunyikan uncertainty hanya menghasilkan file berformat benar dengan klaim yang tidak terbukti.

## Submission dan interview

code.zip terakhir sudah diperiksa; jangan menyebutnya final submission lengkap selama output.csv belum ada. Required evaluation/usage reports tersedia, tetapi final usage harus merujuk tepat run penghasil output yang benar-benar dipilih. log.txt adalah transcript append-only; agent-trace.zip harus mencakup native session files setelah sesi selesai dan app ditutup, dengan secret review sesuai agent_trace_instructions.md. Hindari menyalin trace aktif.

Interview sebaiknya mendemonstrasikan satu investigasi nyata dengan tool results memengaruhi langkah berikutnya, satu penolakan proposal yang benar, dan metrik novelty/output delta. Nyatakan nol incremental sample gain jika memang nol. Kemampuan agent dan kualitas safety dapat dijelaskan tanpa klaim bahwa AI menyelesaikan kasus yang masih unresolved.

Audit ini menambah dokumentasi dan percobaan read-only kecil saja. Tidak mengubah prediction logic, dataset, model budget, source archive atau publication gate.
