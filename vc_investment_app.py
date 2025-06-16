import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Setup Google Sheets connection
def connect_to_user_sheet(sheet_input, worksheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    try:
        if "docs.google.com" in sheet_input:
            sheet_id = sheet_input.split("/d/")[1].split("/")[0]
            sheet = client.open_by_key(sheet_id)
        else:
            sheet = client.open(sheet_input)

        worksheet = sheet.worksheet(worksheet_name)
        return worksheet
    except Exception as e:
        st.error(f"❌ Error accessing Google Sheet: {e}")
        return None

# App UI
def main():
    st.set_page_config(page_title="VC Investment Calculator", layout="centered")
    st.title("\U0001F4BC VC Investment Calculator")
    st.subheader("Estimate Ownership, Dilution & Exit Value")

    st.markdown("### 📄 Google Sheet Setup")
    sheet_url_or_name = st.text_input(
        "Paste Google Sheet name or URL",
        help="Make sure the sheet is shared with the service account email."
    )
    worksheet_name = st.text_input("Worksheet name (optional)", value="Sheet1")

    with st.form("input_form"):
        st.markdown("### Fund Information")
        fund_size = st.number_input("Total fund size ($)", min_value=0.0, step=100000.0, value=2000000.0)

        st.markdown("### Round 1 (Initial Investment)")
        your_investment = st.number_input("Your investment ($)", min_value=0.0, step=1000.0, value=50000.0)
        total_raised_r1 = st.number_input("Total raised in Round 1 ($)", min_value=0.0, step=1000.0, value=500000.0)
        pre_money_r1 = st.number_input("Pre-money valuation Round 1 ($)", min_value=0.0, step=100000.0, value=20000000.0)

        include_round_2 = st.checkbox("Include Round 2 (Future Fundraising)?", value=True)

        new_raise = pre_money_r2 = 0.0
        if include_round_2:
            st.markdown("### Round 2 (New Fundraising)")
            new_raise = st.number_input("New funds raised in Round 2 ($)", min_value=0.0, step=1000.0, value=2000000.0)
            pre_money_r2 = st.number_input("Pre-money valuation Round 2 ($)", min_value=0.0, step=100000.0, value=50000000.0)

        submitted = st.form_submit_button("Calculate")

    if submitted:
        post_money_r1 = pre_money_r1 + total_raised_r1
        ownership_r1 = your_investment / post_money_r1

        if include_round_2 and new_raise > 0 and pre_money_r2 > 0:
            post_money_r2 = pre_money_r2 + new_raise
            diluted_ownership = ownership_r1 * (pre_money_r2 / post_money_r2)

            target_valuation = fund_size / diluted_ownership
            pro_rata_investment = ownership_r1 * new_raise
            loss_percent = (1 - diluted_ownership / ownership_r1) * 100

            st.markdown("### \U0001F4CA Results")
            st.metric("Initial Ownership", f"{ownership_r1 * 100:.4f}%")
            st.metric("Ownership After Dilution", f"{diluted_ownership * 100:.4f}%")
            st.metric("Ownership Decrease", f"{loss_percent:.2f}%")

            st.markdown("---")
            st.metric(f"Company Value Needed to Return Entire Fund (${fund_size:,.0f})", f"${target_valuation:,.0f}")
            st.metric("Pro-Rata Investment in Round 2", f"${pro_rata_investment:,.2f}")
        else:
            target_valuation = fund_size / ownership_r1
            st.markdown("### \U0001F4CA Results")
            st.metric("Initial Ownership", f"{ownership_r1 * 100:.4f}%")
            st.metric(f"Company Value Needed to Return Entire Fund (${fund_size:,.0f})", f"${target_valuation:,.0f}")

        if sheet_url_or_name:
            worksheet = connect_to_user_sheet(sheet_url_or_name, worksheet_name)
            if worksheet:
                try:
                    worksheet.append_row([
                        fund_size,
                        your_investment, total_raised_r1, pre_money_r1,
                        new_raise if include_round_2 else "N/A",
                        pre_money_r2 if include_round_2 else "N/A",
                        ownership_r1,
                        diluted_ownership if include_round_2 else "N/A",
                        target_valuation,
                        pro_rata_investment if include_round_2 else "N/A"
                    ])
                    st.success("✅ Results logged to Google Sheet")
                except Exception as e:
                    st.error(f"❌ Failed to write to Google Sheet: {e}")

if __name__ == "__main__":
    main()
