import csv

file1 = "1.csv"
file2 = "2.csv"
output = "1_with_grades.csv"

SOURCE_COL_NAME = "grade_source_line"

# ---------------------------------
# 1. Read 2.csv and find header row
# ---------------------------------
with open(file2, newline="", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=";")
    rows = list(reader)

header = None
header_row_index = None

for i, row in enumerate(rows):
    cleaned = [cell.strip() for cell in row]
    if "ΑΜ1" in cleaned and "total" in cleaned:
        header = cleaned
        header_row_index = i
        break

if header is None:
    raise RuntimeError("❌ Could not find header row with ΑΜ1 and total")

am1_idx = header.index("ΑΜ1")
am2_idx = header.index("ΑΜ2")
total_idx = header.index("total")

print(f"📌 Header found in 2.csv at line {header_row_index + 1}")
print(f"AM1={am1_idx}, AM2={am2_idx}, total={total_idx}\n")

# ---------------------------------
# 2. Build AM → (grade, source_line)
# ---------------------------------
am_to_grade = {}

for line_no, row in enumerate(rows[header_row_index + 1:], start=header_row_index + 2):
    if len(row) <= total_idx:
        continue

    am1 = row[am1_idx].strip()
    am2 = row[am2_idx].strip()
    grade = row[total_idx].strip()

    print(f"[2.csv] Line {line_no} | AM1={am1}, AM2={am2}, GRADE={grade}")

    if grade:
        if am1 and am1 != "-":
            am_to_grade[am1] = (grade, line_no)
        if am2 and am2 != "-":
            am_to_grade[am2] = (grade, line_no)

print(f"\n✅ Grades collected for {len(am_to_grade)} AMs\n")

# ---------------------------------
# 3. Read 1.csv
# ---------------------------------
with open(file1, newline="", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=";")
    rows1 = list(reader)

header1 = rows1[0]

am_idx = header1.index("AM")
grade_idx = header1.index("grade")

# Add new column if not exists
if SOURCE_COL_NAME not in header1:
    header1.append(SOURCE_COL_NAME)
    for row in rows1[1:]:
        row.append("")

source_idx = header1.index(SOURCE_COL_NAME)

print(f"📌 1.csv → AM={am_idx}, grade={grade_idx}, source_line={source_idx}\n")

# ---------------------------------
# 4. Update grades + source line
# ---------------------------------
for line_no, row in enumerate(rows1[1:], start=2):
    if len(row) <= source_idx:
        continue

    am = row[am_idx].strip()

    if am in am_to_grade:
        grade, src_line = am_to_grade[am]
        print(f"[MATCH] 1.csv line {line_no} | AM={am} → Grade={grade} (from 2.csv line {src_line})")
        row[grade_idx] = grade
        row[source_idx] = str(src_line)
    else:
        print(f"[NO MATCH] 1.csv line {line_no} | AM={am}")

# ---------------------------------
# 5. Write output
# ---------------------------------
with open(output, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";")
    writer.writerows(rows1)

print("\n🎉 DONE")
print(f"📄 Output file: {output}")
