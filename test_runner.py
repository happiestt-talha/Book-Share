"""
BookShare — Manual Test Checklist
Run: python test_runner.py
This prints the checklist. Tick each one manually in your browser.
"""

tests = [
    ("TC001", "Member Registration",
     "Go to /auth/register → fill valid details → submit",
     "Account created, redirected to browse with welcome flash"),

    ("TC002", "Member Login",
     "Go to /auth/login → enter valid credentials → submit",
     "Logged in, welcome flash shown, navbar shows user name"),

    ("TC003", "Add Physical Book",
     "Login → /books/add → fill form, select Physical, add location → submit",
     "Book listed, appears in /books/my with Available badge"),

    ("TC004", "Add Digital Book",
     "Login → /books/add → fill form, select Digital, upload PDF → submit",
     "Book listed, PDF stored, appears in /books/my"),

    ("TC005", "Search Books",
     "Go to /books/ → type a title in search → Apply",
     "Matching books shown in results"),

    ("TC006", "Request Physical Book",
     "Login as different user → browse → click physical book → Request to Borrow → fill date/time/location → send",
     "Flash: request sent. Book status → Pending"),

    ("TC007", "Request Digital Book",
     "Login as different user → browse → click digital book → Request to Borrow → send",
     "No schedule form shown. Request sent. Book status → Pending"),

    ("TC008", "View My Shared Books",
     "Login → /books/dashboard → My Books tab",
     "All listed books shown with type and status badges"),

    ("TC009", "View Borrowed Books",
     "Login as borrower → /books/dashboard → Borrowed Books tab",
     "Active borrows shown with return deadline info"),

    ("TC010", "Accept Borrow Request",
     "Login as owner → /books/dashboard → Requests tab → Accept",
     "Book status → Borrowed. Borrower gets notification"),

    ("TC011", "Reject Borrow Request",
     "Login as owner → Requests tab → Reject",
     "Book status → Available. Borrower gets notification"),

    ("TC012", "Mark Physical Book Returned",
     "Login as owner → Borrowed Books tab → Mark Returned on physical book",
     "Book status → Available. Borrower notified"),

    ("TC013", "Mark Digital Book Returned",
     "Login as borrower → Borrowed Books tab → Mark Returned on digital book",
     "Access revoked. Book status → Available"),

    ("TC014", "Manage Profile",
     "Login → /auth/profile → update name and city → Save",
     "Profile updated. City shows on profile card"),

    ("TC015", "Admin: Edit Any Book",
     "Login as admin → /admin/books → click Edit on any book → change author → save",
     "Change visible on book detail page"),

    ("TC016", "Admin: Block User",
     "Login as admin → /admin/users → Block a member",
     "User shows as Blocked. That user cannot log in"),

    ("TC017", "Admin: View Reports",
     "Login as admin → /admin/reports",
     "Bar charts and doughnut charts render with correct data"),

    ("TC018", "Admin: Remove Content",
     "Login as admin → /admin/books → Delete a book",
     "Book removed from browse. Owner gets notification"),
]

print("\n" + "="*70)
print("  BOOKSHARE — TEST CASE CHECKLIST")
print("="*70)

passed = 0
failed = 0
for tc_id, name, steps, expected in tests:
    print(f"\n[{tc_id}] {name}")
    print(f"  Steps:    {steps}")
    print(f"  Expected: {expected}")
    result = input("  Result (p=pass / f=fail / s=skip): ").strip().lower()
    if result == 'p':
        print(f"  ✅ PASS")
        passed += 1
    elif result == 'f':
        note = input("  Note (what went wrong): ")
        print(f"  ❌ FAIL — {note}")
        failed += 1
    else:
        print(f"  ⏭  SKIPPED")

print("\n" + "="*70)
print(f"  RESULTS: {passed} PASSED  |  {failed} FAILED  |  {18 - passed - failed} SKIPPED")
print("="*70 + "\n")