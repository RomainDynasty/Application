# streamlit_app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import plotly.express as px
import plotly.graph_objects as go

# Import your classes
from portfolio_analyzer import PortfolioAnalyzer

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Streamlit configuration
st.set_page_config(
    page_title="Portfolio Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Cache for data
@st.cache_data(ttl=3600)
def load_and_analyze_portfolio(config_path: str):
    """Load and analyze portfolio"""
    logger.info("Loading data...")
    analyzer = PortfolioAnalyzer(config_path)
    results = analyzer.run_full_analysis()
    return results, analyzer.df, analyzer.df_complete


def main():
    # Main header
    st.title("📊 Dynasty Global Convertible Fund")
    st.subheader(f"Analysis Report - {datetime.now().strftime('%d/%m/%Y')}")
    
    # Load data
    try:
        with st.spinner("🔄 Loading and analyzing..."):
            results, df_filtered, df_complete = load_and_analyze_portfolio("config.ini")
        st.success(f"✅ Data loaded! {len(df_complete)} positions analyzed")
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.stop()

    st.divider()
    
    # Create tabs
    tab1, tab2 = st.tabs(["📈 Portfolio Metrics", "📊 Interactive Charts"])
    
    # ========================================
    # TAB 1: PORTFOLIO METRICS
    # ========================================
    with tab1:
        display_portfolio_metrics(results, df_filtered, df_complete)
    
    # ========================================
    # TAB 2: INTERACTIVE CHARTS
    # ========================================
    with tab2:
        display_interactive_charts(df_complete)


def display_portfolio_metrics(results, df_filtered, df_complete):
    """Display main portfolio metrics"""
    
    # Key metrics at top
    st.header("🎯 Main Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Holdings", results['holding'])
    with col2:
        st.metric("Equity Sensi Contrib", f"{results['contrib_equity_sensi']:.2f}%")
    with col3:
        st.metric("Average Premium", f"{results['premium']:.2f}%")
    with col4:
        st.metric("Portfolio Rating", results['rating'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Duration", f"{results['contrib_duration']:.2f}")
    with col2:
        st.metric("Rate Sensi", f"{results['contrib_taux_sensi']:.2f}%")
    with col3:
        st.metric("Credit Sensi", f"{results['contrib_credit_sensi']:.2f}%")
    with col4:
        st.metric("Credit Spread", f"{results['credit_spread']:.0f} bps")
    
    st.divider()
    
    # Top Holdings
    st.header("🏆 Top Holdings")
    
    # Top 10 by Market Value
    st.subheader("Top 10 by Market Value")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        df_top10 = results['top_10_holdings'].iloc[:-1]  # Exclude TOTAL row
        st.dataframe(
            results['top_10_holdings'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        fig = px.bar(
            df_top10,
            y='Short Name',
            x='Market Value (%)',
            orientation='h',
            title="Top 10 Holdings",
            text='Market Value (%)'
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Top 10 Equity Contributors
    st.subheader("Top 10 Equity Contributors")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        df_contrib = results['top_10_contrib_equity'].iloc[:-1]  # Exclude TOTAL row
        st.dataframe(
            results['top_10_contrib_equity'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        fig = px.bar(
            df_contrib,
            y='Short Name',
            x='CONTRIB SENSI EQUITY',
            orientation='h',
            title="Top 10 Equity Contributors",
            text='CONTRIB SENSI EQUITY',
            color='CONTRIB SENSI EQUITY',
            color_continuous_scale='Blues'
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Allocations by categories
    st.header("📊 Allocations")
    
    # By Sector
    st.subheader("By Sector")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            results['contrib_by_sector'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        fig = px.bar(
            results['contrib_by_sector'],
            x='Industry Sector',
            y='CONTRIB SENSI EQUITY',
            title="Contribution by Sector",
            color='CONTRIB SENSI EQUITY',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=400, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # By Region
    st.subheader("By Region")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            results['contrib_by_region'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        fig = px.pie(
            results['contrib_by_region'],
            values='CONTRIB SENSI EQUITY',
            names='REGION',
            title="Allocation by Region"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # By Theme
    st.subheader("By Theme")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            results['contrib_by_theme'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        fig = px.bar(
            results['contrib_by_theme'],
            x='Theme',
            y='CONTRIB SENSI EQUITY',
            title="Contribution by Theme",
            color='CONTRIB SENSI EQUITY',
            color_continuous_scale='Teal'
        )
        fig.update_layout(height=400, showlegend=False, xaxis_tickangle=-45, )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # By Style
    st.subheader("By Style")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            results['contrib_by_style'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        fig = px.pie(
            results['contrib_by_style'],
            values='CONTRIB SENSI EQUITY',
            names='Style',
            title="Allocation by Style",
            hole=0.3
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Buckets
    st.header("📦 Bucket Analysis")
    
    # Sensi Buckets
    st.subheader("Sensitivity Buckets")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            results['contrib_by_sensi_bucket'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        # Custom order for buckets
        ordre_sensi = ["Bucket 0-25", "Bucket 25-50", "Bucket 50-75", "Bucket 75-100"]
        df_sensi = results['contrib_by_sensi_bucket'].copy()
        df_sensi['SENSI BUCKET'] = pd.Categorical(
            df_sensi['SENSI BUCKET'],
            categories=ordre_sensi,
            ordered=True
        )
        df_sensi = df_sensi.sort_values('SENSI BUCKET')
        
        fig = px.bar(
            df_sensi,
            x='SENSI BUCKET',
            y='Total_Contrib',
            title="Distribution by Sensitivity Bucket",
            text='Total_Contrib',
            color='Total_Contrib',
            color_continuous_scale='RdYlGn'
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Volatility Buckets
    st.subheader("Volatility Buckets")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            results['contrib_by_vol_bucket'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        # Custom order for volatility
        ordre_vol = ["<20%", "20-30%", "30-40%", ">40%"]
        df_vol = results['contrib_by_vol_bucket'].copy()
        df_vol['Vol_Bucket'] = pd.Categorical(
            df_vol['Vol_Bucket'],
            categories=ordre_vol,
            ordered=True
        )
        df_vol = df_vol.sort_values('Vol_Bucket')
        
        fig = px.bar(
            df_vol,
            x='Vol_Bucket',
            y='Total_Contrib',
            title="Distribution by Volatility",
            text='Total_Contrib',
            color='Total_Contrib',
            color_continuous_scale='Reds'
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Credit Analysis
    st.header("💳 Credit Analysis")
    
    credit_analysis = results['credit_analysis']
    
    # By Category (IG/HY/Cash)
    st.subheader("By Category (IG/HY/Cash)")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            credit_analysis['by_category'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        fig = px.pie(
            credit_analysis['by_category'],
            values='Market_Value',
            names='Credit Category',
            title="IG/HY/Cash Allocation",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # By S&P Rating
    st.subheader("By S&P Rating")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            credit_analysis['by_rating'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        fig = px.bar(
            credit_analysis['by_rating'],
            x='S&P Ajusted',
            y='Market_Value',
            title="Allocation by Rating",
            text='Market_Value',
            color='Market_Value',
            color_continuous_scale='RdYlGn_r'
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Top 10 Issuers
    st.subheader("Top 10 Issuers")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            credit_analysis['by_issuer'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        fig = px.bar(
            credit_analysis['by_issuer'],
            y='Issuer',
            x='Market Value (%)',
            orientation='h',
            title="Top 10 Issuers",
            text='Market Value (%)',
            color='Market Value (%)',
            color_continuous_scale='Blues'
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # By Maturity
    st.subheader("By Maturity")
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            credit_analysis['by_maturity'],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    with col2:
        # Custom order for maturity
        ordre_mat = ["<1 An", "1 à 3 Ans", "3 à 5 Ans", ">5 Ans"]
        df_mat = credit_analysis['by_maturity'].copy()
        df_mat['Maturity_Bucket'] = pd.Categorical(
            df_mat['Maturity_Bucket'],
            categories=ordre_mat,
            ordered=True
        )
        df_mat = df_mat.sort_values('Maturity_Bucket')
        
        fig = px.bar(
            df_mat,
            x='Maturity_Bucket',
            y='Market_Value',
            title="Allocation by Maturity",
            text='Market_Value',
            color='Market_Value',
            color_continuous_scale='Purples'
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Detailed view Maturity x Rating (Heatmap)
    st.subheader("Detailed View: Maturity x Rating")
    
    # Create heatmap
    df_heatmap = credit_analysis['by_maturity_rating'].pivot_table(
        index='S&P Ajusted',
        columns='Maturity_Bucket',
        values='Market_Value',
        fill_value=0
    )
    
    # Reorder columns
    ordre_mat = ["<1 An", "1 à 3 Ans", "3 à 5 Ans", ">5 Ans"]
    df_heatmap = df_heatmap.reindex(columns=[col for col in ordre_mat if col in df_heatmap.columns])
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(
            credit_analysis['by_maturity_rating'],
            use_container_width=True,
            hide_index=True,
            height=500
        )
    
    with col2:
        fig = px.imshow(
            df_heatmap,
            labels=dict(x="Maturity", y="Rating", color="Market Value (%)"),
            title="Heatmap Maturity x Rating",
            color_continuous_scale='YlOrRd',
            aspect="auto"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Detailed contributions by theme
    with st.expander("🎨 Detailed Contributions by Theme"):
        st.dataframe(
            results['contrib_by_theme_name'],
            use_container_width=True
        )


def display_interactive_charts(DF_DYN_CONV_PORT):
    """Display interactive charts with filters"""
    
    # Sidebar for filters
    st.sidebar.header("⚙️ Filter Settings")

    # Option to enable/disable filters
    enable_filters = st.sidebar.checkbox("Enable filters", value=False)

    # Initialize filtered dataframe
    df_filtered = DF_DYN_CONV_PORT.copy()

    # Conditional filters
    if enable_filters:
        df_filter_working = DF_DYN_CONV_PORT.copy()

        security_types = st.sidebar.multiselect(
            "Security Type:",
            options=list(DF_DYN_CONV_PORT["Security Type"].dropna().unique())
        )

        industry_sectors = st.sidebar.multiselect(
            "Industry Sector:",
            options=list(DF_DYN_CONV_PORT["Industry Sector"].dropna().unique())
        )

        region = st.sidebar.multiselect(
            "Region:",
            options=list(DF_DYN_CONV_PORT["REGION"].dropna().unique())
        )

        theme = st.sidebar.multiselect(
            "Theme:",
            options=list(DF_DYN_CONV_PORT["Theme"].dropna().unique())
        )

        sensi_bucket = st.sidebar.multiselect(
            "Sensi Bucket:",
            options=list(DF_DYN_CONV_PORT["SENSI BUCKET"].dropna().unique())
        )

        vol_bucket = st.sidebar.multiselect(
            "Vol Bucket:",
            options=list(DF_DYN_CONV_PORT["Vol_Bucket"].dropna().unique())
        )

        maturity_bucket = st.sidebar.multiselect(
            "Maturity Bucket:",
            options=list(DF_DYN_CONV_PORT["Maturity_Bucket"].dropna().unique())
        )

        credit_category = st.sidebar.multiselect(
            "Credit Category:",
            options=list(DF_DYN_CONV_PORT["Credit Category"].dropna().unique())
        )

        rating = st.sidebar.multiselect(
            "Rating:",
            options=list(DF_DYN_CONV_PORT["S&P Ajusted"].dropna().unique())
        )

        style = st.sidebar.multiselect(
            "Style:",
            options=list(DF_DYN_CONV_PORT["Style"].dropna().unique())
        )
       
        # Apply filters
        if security_types:
            df_filter_working = df_filter_working[df_filter_working["Security Type"].isin(security_types)]
        if industry_sectors:
            df_filter_working = df_filter_working[df_filter_working["Industry Sector"].isin(industry_sectors)]
        if region:
            df_filter_working = df_filter_working[df_filter_working["REGION"].isin(region)]
        if theme:
            df_filter_working = df_filter_working[df_filter_working["Theme"].isin(theme)]
        if sensi_bucket:
            df_filter_working = df_filter_working[df_filter_working["SENSI BUCKET"].isin(sensi_bucket)]
        if vol_bucket:
            df_filter_working = df_filter_working[df_filter_working["Vol_Bucket"].isin(vol_bucket)]
        if maturity_bucket:
            df_filter_working = df_filter_working[df_filter_working["Maturity_Bucket"].isin(maturity_bucket)]
        if credit_category:
            df_filter_working = df_filter_working[df_filter_working["Credit Category"].isin(credit_category)]
        if rating:
            df_filter_working = df_filter_working[df_filter_working["S&P Ajusted"].isin(rating)]
        if style:
            df_filter_working = df_filter_working[df_filter_working["Style"].isin(style)]
            
        df_filtered = df_filter_working.copy()
    else:
        df_filtered = DF_DYN_CONV_PORT.copy()

    # Sort
    st.sidebar.header("🔄 Sort Settings")
    sort_order = st.sidebar.selectbox(
        "Sort by:",
        ["No sorting", "Market Value (%)", "CONTRIB SENSI EQUITY", "Expected Life (Fugit)"]
    )

    if sort_order == "Market Value (%)":
        df_filtered = df_filtered.sort_values("Market Value (%)", ascending=False)
    elif sort_order == "CONTRIB SENSI EQUITY":
        df_filtered = df_filtered.sort_values("CONTRIB SENSI EQUITY", ascending=False)
    elif sort_order == "Expected Life (Fugit)":
        df_filtered = df_filtered.sort_values("Expected Life (Fugit)", ascending=True)


    st.header("Visualizations")
    
    st.sidebar.header("📊 Chart Settings")
    chart_type = st.sidebar.selectbox(
        "Chart type:",
        ["Pie", "Bar", "Barh", "Stacked Bar", "Squarify"]
    )

    value_y = st.sidebar.selectbox(
        "Values (Y-axis):",
        ["Market Value (%)", "CONTRIB SENSI EQUITY"]
    )

    value_x = st.sidebar.selectbox(
        "Grouping (X-axis):",
        ["Security Type", "Industry Sector", "REGION", "Theme", "SENSI BUCKET", 
        "Vol_Bucket", "Maturity_Bucket", "Credit Category", "S&P Ajusted", "Style", "Short Name"]
    )

    value_stack = st.sidebar.selectbox(
        "Stack parameter:",
        ["None", "Security Type", "Industry Sector", "REGION", "Theme", "SENSI BUCKET", 
        "Vol_Bucket", "Maturity_Bucket", "Credit Category", "S&P Ajusted", "Style", "Short Name"]
    )

    st.subheader(f"{value_y} by {value_x}")

    # Define custom orders for axes
    custom_order = {
        "SENSI BUCKET": ["Bucket 0-25", "Bucket 25-50", "Bucket 50-75", "Bucket 75-100"],
        "Vol_Bucket": ["<20%", "20-30%", "30-40%", ">40%"],
        "Maturity_Bucket": ["<1 An", "1 à 3 Ans", "3 à 5 Ans", ">5 Ans"],
        "S&P Ajusted": ["AAA", "AA+", "AA", "AA-", 
                    "A+", "A", "A-", 
                    "BBB+", "BBB", "BBB-", 
                    "BB+", "BB", "BB-", 
                    "B+", "B", "B-", 
                    "CCC+", "CCC", "CCC-", 
                    "CC", "C", "D", 
                    "NR", "CASH"]
    }

    try:
        # Aggregate data
        df_graph = df_filtered.groupby(value_x)[value_y].sum()
        
        # Apply custom order if available
        if value_x in custom_order:
            present_categories = [cat for cat in custom_order[value_x] if cat in df_graph.index]
            df_graph = df_graph.reindex(present_categories).dropna()
        else:
            df_graph = df_graph.sort_values(ascending=False)
        
        # Calculate number of lines per category
        df_count = df_filtered.groupby(value_x).size()
        df_count = df_count.reindex(df_graph.index).fillna(0).astype(int)
        
        # Create summary table
        df_recap = pd.DataFrame({
            value_x: df_graph.index,
            value_y: df_graph.values,
            "Number of lines": df_count.values
        })
        
        # Layout in 2 columns
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.markdown("<h4 style='text-align: center;'>Summary Table</h4>", unsafe_allow_html=True)
            st.dataframe(
                df_recap,
                use_container_width=True,
                height=500,
                column_config={
                    value_y: st.column_config.NumberColumn(
                        value_y,
                        format="%.2f"
                    ),
                    "Number of lines": st.column_config.NumberColumn(
                        "Number of lines",
                        format="%d"
                    )
                }
            )
        
        with col2:
            if chart_type == "Stacked Bar" and value_stack == "None":
                st.warning("⚠️ Please select a stack parameter")
            else:
                if chart_type == "Pie":
                    fig = px.pie(
                        values=df_graph.values,
                        names=df_graph.index,
                        title=f"{value_y} by {value_x}"
                    )
                    fig.update_layout(title_x=0.30, height=500)
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Bar":
                    df_bar = pd.DataFrame({
                        value_x: df_graph.index,
                        value_y: df_graph.values
                    })
                    
                    fig = px.bar(
                        df_bar,
                        x=value_x,
                        y=value_y,
                        title=f"{value_y} by {value_x}"
                    )
                    
                    if value_x in custom_order:
                        present_categories = [cat for cat in custom_order[value_x] if cat in df_graph.index]
                        fig.update_xaxes(categoryorder='array', categoryarray=present_categories)
                    
                    fig.update_layout(title_x=0.30, height=500)
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Barh":
                    df_barh = pd.DataFrame({
                        value_x: df_graph.index[::-1],
                        value_y: df_graph.values[::-1]
                    })
                    
                    fig = px.bar(
                        df_barh,
                        x=value_y,
                        y=value_x,
                        orientation='h',
                        title=f"{value_y} by {value_x}"
                    )
                    
                    if value_x in custom_order:
                        present_categories = [cat for cat in custom_order[value_x] if cat in df_graph.index]
                        fig.update_yaxes(categoryorder='array', categoryarray=present_categories[::-1])
                    
                    fig.update_layout(title_x=0.30, height=500)
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "Stacked Bar":
                    df_stacked = df_filtered.groupby([value_x, value_stack])[value_y].sum().reset_index()
                    
                    if value_x in custom_order:
                        present_categories = [cat for cat in custom_order[value_x] 
                                            if cat in df_stacked[value_x].unique()]
                        df_stacked[value_x] = pd.Categorical(
                            df_stacked[value_x],
                            categories=present_categories,
                            ordered=True
                        )
                    
                    if value_stack in custom_order:
                        stack_categories = [cat for cat in custom_order[value_stack] 
                                        if cat in df_stacked[value_stack].unique()]
                        df_stacked[value_stack] = pd.Categorical(
                            df_stacked[value_stack],
                            categories=stack_categories,
                            ordered=True
                        )
                    
                    df_stacked = df_stacked.sort_values([value_x, value_stack])
                    
                    fig = px.bar(
                        df_stacked,
                        x=value_x,
                        y=value_y,
                        color=value_stack,
                        title=f"{value_y} by {value_x} (stacked by {value_stack})"
                    )
                    
                    fig.update_layout(title_x=0.5, height=500)
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type == "Squarify":
                    fig = px.treemap(
                        names=df_graph.index,
                        parents=[""] * len(df_graph),
                        values=df_graph.values,
                        title=f"{value_y} by {value_x}"
                    )
                    fig.update_layout(title_x=0.30, height=500)
                    st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error creating chart: {str(e)}")
        logger.error(f"Chart error: {e}", exc_info=True)

    st.divider()
    
    # Filtered data table
    st.subheader("📋 Detailed Data")
    st.dataframe(df_filtered, use_container_width=True)


if __name__ == "__main__":
    main()