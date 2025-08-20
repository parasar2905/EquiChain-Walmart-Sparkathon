import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="EqualChain: ESG + DEI Dashboard", layout="wide")
st.title("🌱 EqualChain: ESG + DEI Supplier Intelligence Platform")

st.markdown("""
This advanced platform auto-appends multiple supplier files, evaluates their ESG + DEI performance, and provides dynamic filtering, visual insights, and location mapping.
---
""")

# ------------------- Upload & Append -------------------
uploaded_files = st.file_uploader("📤 Upload One or More Supplier CSV Files", type="csv", accept_multiple_files=True)

required_cols = ["ID", "Ownership_Type", "Packaging_Type", "CO2_Emission_kg_per_unit", "Certification", "Locality"]

dfs = []
if uploaded_files:
    for file in uploaded_files:
        try:
            df_temp = pd.read_csv(file)
            # Standardize column names
            df_temp.columns = [c.strip().replace(" ", "_") for c in df_temp.columns]
            # Check for required columns
            if not all(col in df_temp.columns for col in required_cols):
                st.warning(f"Skipping {file.name}: missing required columns.")
                continue
            st.write(f"**Preview of `{file.name}`:**")
            st.dataframe(df_temp.head())
            dfs.append(df_temp)
            st.info(f"{file.name}: {len(df_temp)} rows loaded.")
        except Exception as e:
            st.error(f"❌ Error loading {file.name}: {e}")
    if dfs:
        df = pd.concat(dfs, ignore_index=True).drop_duplicates()
        st.success(f"Loaded {len(dfs)} files. Total rows: {len(df)}")
        st.download_button("Download All Supplier Data", df.to_csv(index=False), file_name="All_Suppliers.csv")
        st.write("**Preview of merged data:**")
        st.dataframe(df.head())
    else:
        st.error("No valid files uploaded. Please upload CSVs with the required columns.")
        st.stop()
else:
    df = pd.read_csv("C:\\Users\\paras\\Downloads\\EquiChain Walmart Sparkathon\\EqualChain_Merged_Cleaned_Final.csv")
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]

if 'df' not in locals() or df.empty:
    st.error("No valid data available. Please upload at least one valid supplier CSV file.")
    st.stop()

# Column type check
if not pd.api.types.is_numeric_dtype(df['CO2_Emission_kg_per_unit']):
    st.warning("Column 'CO2_Emission_kg_per_unit' is not numeric. Please check your data.")

# ------------------- Scoring -------------------
def calculate_scores(df):
    def dei_score(row):
        score = 0
        if 'Women' in str(row.get('Ownership_Type')): score += 2
        if 'Minority' in str(row.get('Ownership_Type')): score += 2
        return score

    def sustainability_score(row):
        score = 5
        try:
            val = float(row['CO2_Emission_kg_per_unit'])
            score += 2 if val < 200 else 1 if val < 500 else -1
        except:
            pass
        eco = str(row.get('Packaging_Type'))
        if any(x in eco for x in ['Compostable', 'Biodegradable', 'Recycled']):
            score += 2
        return min(max(score, 0), 10)

    def performance_score(row):
        score = 0
        if row.get('Certification') not in ['None', '', None]: score += 1
        if str(row.get('Locality')).lower() == 'local': score += 1
        return score

    df['DEI_Score'] = df.apply(dei_score, axis=1)
    df['Sustainability_Score'] = df.apply(sustainability_score, axis=1)
    df['Performance_Score'] = df.apply(performance_score, axis=1)
    df['EqualChain_Score'] = (df['DEI_Score'] * 0.4 + df['Sustainability_Score'] * 0.4 + df['Performance_Score'] * 0.2).round(2)
    return df

df = calculate_scores(df)

# ------------------- Sidebar Filters -------------------
st.sidebar.header("🔎 Filter Suppliers")
ownership = st.sidebar.multiselect("Ownership Type", df['Ownership_Type'].dropna().unique())
packaging = st.sidebar.multiselect("Packaging Type", df['Packaging_Type'].dropna().unique())
cert = st.sidebar.multiselect("Certification", df['Certification'].dropna().unique())
local = st.sidebar.multiselect("Locality", df['Locality'].dropna().unique())
max_co2 = st.sidebar.slider("Max CO₂ Emission (kg/unit)", 
    float(df['CO2_Emission_kg_per_unit'].min()), float(df['CO2_Emission_kg_per_unit'].max()),
    float(df['CO2_Emission_kg_per_unit'].max()))

filtered = df.copy()
if ownership: filtered = filtered[filtered['Ownership_Type'].isin(ownership)]
if packaging: filtered = filtered[filtered['Packaging_Type'].isin(packaging)]
if cert: filtered = filtered[filtered['Certification'].isin(cert)]
if local: filtered = filtered[filtered['Locality'].isin(local)]
filtered = filtered[filtered['CO2_Emission_kg_per_unit'] <= max_co2]

# ------------------- Tabs -------------------
tab1, tab2, tab3, tab4 = st.tabs(["🏆 Rankings", "📈 Charts", "🗺 Map View", "🧾 Raw Data"])

with tab1:
    st.subheader("🏁 Top Ranked Suppliers")
    top_suppliers = filtered.sort_values(by='EqualChain_Score', ascending=False)
    st.dataframe(top_suppliers[['ID', 'Ownership_Type', 'Packaging_Type', 'CO2_Emission_kg_per_unit', 'Certification', 'Locality', 'EqualChain_Score']], use_container_width=True)
    st.download_button("📥 Download Filtered List", top_suppliers.to_csv(index=False), file_name="Filtered_Suppliers.csv")

with tab2:
    st.subheader("📊 Visual Insights")
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.bar(top_suppliers.head(10), x='ID', y='EqualChain_Score', color='Ownership_Type', title="Top 10 Supplier Scores")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        pie_fig = px.pie(filtered, names='Ownership_Type', title="Ownership Distribution")
        st.plotly_chart(pie_fig, use_container_width=True)

with tab3:
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        st.subheader("🗺 Supplier Map (Geocoded)")
        st.map(filtered[['Latitude', 'Longitude']].dropna())
    else:
        st.info("📍 No geolocation data found in dataset. Add 'Latitude' and 'Longitude' columns to enable this feature.")

with tab4:
    st.subheader("📄 Raw Uploaded Data")
    st.dataframe(df, use_container_width=True)

# ------------------- Footer -------------------
st.markdown("---")
st.caption("Built with 💚 for Walmart Sparkathon 2025 by Team EliteCoders")