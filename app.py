import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px

st.set_page_config(page_title="Uber analytics",layout="wide")

#load Database

df=pd.read_csv("uber.csv")

# sidebar menu

with st.sidebar:
    select= option_menu("Main Menu",["Dashboard","Dataset","Overview","Ride Analytics","Data Assistant"],
                        icons=["Home","table","bar-chart","graph-up","robot"],
                        menu_icon="car-front",default_index=0
                        )

if select =="Dataset":
    st.title("Dataset Explorer")
    st.divider()

    #dataset overview

    col1,col2,col3 = st.columns(3)

    col1.metric("Total Rows",df.shape[0])
    col2.metric ("Total Columns",df.shape[1])
    col3.metric("Missing Values",df.isna().sum().sum())

    st.divider()

    #columns section

    st.subheader("Select Colums")
    selected_columns=st.multiselect("Choose columns to display",
                                    df.columns,default=df.columns)
    filtered_df=df[selected_columns]

    #search dataset

    st.subheader("Search in Dataset")
    search_value=st.text_input("Search Any Values")
    if search_value:
        filtered_df = filtered_df[filtered_df.astype(str).apply(
            lambda row:row.str.contains(search_value,case=False).any(),axis=1)]
    #column Filter
    st.subheader("Column Filter")

    col1,col2 =st.columns(2)

    with col1:
        filtered_column=st.selectbox("Selcet Column",filtered_df.columns)

    with col2:
        filtered_values= st.selectbox("Select Values",filtered_df[filtered_column].dropna().unique())

    if st.button("Apply Filter"):
        filtered_df=filtered_df[filtered_df[filtered_column]==filtered_values]
        st.divider()

    #row display
    st.subheader("Row Display")

    row=st.slider("Number of rows of dislay",10,len(filtered_df),100)
    st.divider()

    #dataset table

    st.subheader("Dataset Table")

    st.dataframe(filtered_df.head(row),use_container_width=True)

    #show full dataset

    if st.checkbox("Show Full dataset"):
        st.dataframe(filtered_df,use_container_width=True)
    st.divider()

    #columns statics
    st.subheader("Columns Statistics")
    numeric_cols=df.select_dtypes(include=["int64","float64"]).columns

    if len(numeric_cols)>0:
        selected_col=st.selectbox("Select Numeric Columns",numeric_cols)
        st.write(filtered_df[selected_col].describe())
    st.divider()

    st.subheader("Download Data")
    csv= filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Filtered Dataset",csv,"filtered_dataset.csv","text/csv")

if select == "Overview":
    st.title("Uber Operation")
    st.markdown("---")

    #strategic KPI LAYER

    total_ride= len(df)

    completed_ride =df[df["Booking Status"]=="Completed"]

    total_revenue= completed_ride["Booking Value"].sum()

    avg_distance=completed_ride["Ride Distance"].mean()

    success_rate=(len(completed_ride)/total_ride)*100   if total_ride>0 else 0

    avg_rating = completed_ride["Customer Rating"].dropna().mean()

    kpi1, kpi2, kpi3, kpi4 =st.columns(4)

    kpi1.metric("Gross Booking Values",f"{total_revenue:.0f}",
                "Target:1000000")
    kpi2.metric("fulfilment Rate",f"{success_rate:.1f}%",
                "-2.4% From Previous Distance","red")
    kpi3.metric("Avg Customer Rating",f"{avg_rating:.1f}/5.0")
    st.divider()

    #Business Unit Performance

    st.subheader("Business Unit Performance")

    bu_metrics =df.groupby("Vehicle Type").agg(
        Total_Booking=("Booking ID","count"),
        Revenue_generated=("Booking Value","sum"),
        Avg_Distance=("Ride Distance","mean"),
        Avg_rating=("Customer Rating","mean")
    )
    bu_metrics["Revenue Share %"]=(bu_metrics["Revenue_generated"]/total_revenue*100 if total_revenue >0 else 0)

    st.dataframe(
        bu_metrics.style.format({"Revenue_generated":"{:.2f}",
                                "Avg_Distance":"{:.2f}km",
                                 "Avg_Rating": "{:.1f}",
                                 "Revenue Share%":"{:.1f}%"}
                                ).background_gradient(subset=["Revenue_generated","Total_Booking"],cmap="YlGn"),use_container_width=True)
    st.divider()


    #operational efficiency

    col_eff,col_can =st.columns(2)
    with col_eff:
        st.subheader("Operational Efficiency")

        eff_df =df.groupby("Vehicle Type")[["Avg VTAT","Avg CTAT"]].mean()

        st.write("Average Turnaround Time(Minuets)")
        st.dataframe(
            eff_df.style.highlight_max(axis=0,color="#ffccff").highlight_min(axis=0,color="ccddcc"),
            use_container_width=True
        )

    with col_can:
        st.subheader("Cancellation Audit")
        status_count=df["Booking Status"].value_counts().to_frame(name="Count")

        status_count["Share %"]=(status_count["Count"]/total_ride*100)
        st.dataframe(status_count,use_container_width=True)
        st.divider()

    #financial Deep  dive

    st.subheader("Financial Deep Dive")

    pay_col ,reason_col =st.columns([4,6])

    #payment analysis

    with pay_col:
        st.markdown("** Payment Preference")

        pay_summary=(completed_ride["Payment Method"].value_counts(normalize=True)*100)
        st.dataframe(pay_summary.rename("Usage %"),use_container_width=True)

    #cancellation Reason Analysis

    with reason_col:
        st.markdown("**Primary Cancellation Triggers**")
        cust_reasons =(df["Reason for cancelling by Customer"].dropna().value_counts().head(3))

        drv_reasons=(df["Driver Cancellation Reason"].dropna().value_counts().head(3))
        cust_reasons.index="Customer"+cust_reasons.index
        drv_reasons.index="Driver"+drv_reasons.index

        reason_df=pd.concat([cust_reasons,drv_reasons]).to_frame()
        st.dataframe(reason_df)

    #Data Quality Audit

    with st.expander("Data Quality & Audit Logs"):
        audit1,audit2 =st.columns(2)

        audit1.write(f"**Duplicate Records:{df.duplicated().sum()}**")
        audit2.write(f"**Missing Booking Values:{df["Booking Value"].isna().sum()}**")
        st.info("Missing Bookings Value are expected for cancelled or no driver rides")
        st.success("Executive Overview Generated From Operational Dataset")

if select =="Ride Analytics":

    st.title("Advance Ride Intelligence Dashboard")
    st.divider()

    completed =df[df["Booking Status"]=="Completed"]

    #Sunburst Chart

    st.subheader("Revenue Hierarchy")

    fig1= px.sunburst(completed,path=["Vehicle Type","Payment Method"],
                      values="Booking Value",
                      color="Booking Value",
                      color_continuous_scale="hot")

    fig1.update_layout(height=500)

    st.plotly_chart(fig1,use_container_width=True)
    st.divider()

    #Treee map chart

    st.subheader("Revenue Distribution")
    fig2=px.treemap(completed,path=["Vehicle Type","Payment Method"],
                    values="Booking Value",
                    color="Booking Value",
                    color_continuous_scale="purples")
    fig2.update_layout(margin = dict(t=20, l=0 ,r=0 ,b=0),height=420)
    st.plotly_chart(fig2,use_container_width=True)

    st.subheader("Customer Rating Spread")

    fig3=px.box(completed,x="Vehicle Type",y="Customer Rating",color="Vehicle Type")
    fig3.update_layout(showlegend=False,height=420)
    st.plotly_chart(fig3,use_container_width=True)

    #Sankey Diagram

    st.subheader("Ride flow Analysis")
    flow=df.groupby(["Vehicle Type","Booking Status"]).size().reset_index(name="count")
    source_label=flow["Vehicle Type"].unique().tolist()
    target_label=flow["Booking Status"].unique().tolist()

    labels =source_label + target_label

    source = flow["Vehicle Type"].apply(lambda x:labels.index(x)).tolist()
    target =flow["Booking Status"].apply(lambda x:labels.index(x)).tolist()
    value= flow["count"].tolist()

    import plotly.graph_objects as go

    fig4 =go.Figure(data=[go.Sankey(node=dict(pad=15,
                                              thickness=20,
                                              line=dict(color="orchid",width=0.5),label=labels),
                                    link=dict(source=source,
                                              target=target,
                                              value=value)
                                    )])
    fig4.update_layout(height=500)
    st.plotly_chart(fig4,use_container_width=True)

if select =="Data Assistant":
    st.title("Data Assistant")
    st.divider()

    st.write("Ask Question about dataset and get visual analytics")
    user_question=st.text_input("Ask your question")


    def booking():
        status = df["Booking Status"].value_counts()
        fig = px.bar(x=status.index,
                     y=status.values,
                     labels={"x": "Booking status", "y": "Ride Count"},
                     title="Ride Distribution by status")

        st.plotly_chart(fig, use_container_width=True)

    if user_question:
        q= user_question.lower()

        completed = df[df["Booking Status"]=="completed"]

    #total rides


        if"total rides" in q:
            total= len(df)
            st.success(f"Total rides in dataset:{total}")
            st.write("IF you want a total rides graph ,then click")
            st.button("click")

        if st.button:
            booking()


        elif "revenue" in q:
            revenue =completed.groupby("Vehicle Type")["Booking Values"].sum()
            st.success(f"Total Revenue:{revenue.sum():,.2f}")

            fig=px.bar(x=revenue.index,y=revenue.values,
                       title="Revenue by vehicle type",
                       labels={"x":"Vehicle Type","y":"Revenue"})
            st.plotly_chart(fig,use_container_width=True)

        elif"vehicle"  in q:
            vehicle =df["Vehicle Type"].value_counts()
            st.success(f"Most Used Vehicle type:{vehicle.index()}")

            fig=px.pie(names=vehicle.index,values=vehicle.values,title="Vehicle usage distribuation")

            st.plotly_chart(fig,use_container_width=True)

        #payment Analysis

        elif "payment" in q:
            payment=completed["Payment Method"].value_counts()

            fig=px.pie(
                names=payment.index,
                values=payment.values,
                title="Payment Method"
            )
            st.plotly_chart(fig,use_container_width=True)

            #cancellation analysis
            #rating Analysis

        elif "rating" in q:
            fig= px.histogram(completed,
                              x="Customer Rating",
                              nbins=10,
                              title="Customer Rating")
            st.plotly_chart(fig,use_container_width=True)

            st.success(f"Average Rating{completed["Customer Rating"].mean():.2f}")

        elif "distance" in q:
            fig= px.scatter(completed,
                            x="Ride Distance",
                            y="Booking Values",
                            color="Vehicle Type",
                            title="Ride Distance vs Booking values")

            st.plotly_chart(fig,use_container_width=True)

            st.success(f"Average Distance:{completed["Ride Distance"].mean()}:.2f")

        else:
            st.warning("Question not recognized .Try asking about cancellation ,revenue,vehicle type,distance,payment etc")
            st.divider()

if select == "Dashboard":
    st.header("Welcome to dashboard")

    completed = df[df["Booking Status"] == "completed"]

    # col1,col2 =st.columns(2)

    # with col1:
    #     vehicle =completed["Vehicle Type"].value_counts()
    #     fig=px.bar(x=vehicle.index,
    #                y=vehicle.values,
    #                title= "vehicle type is most used")
    #     st.plotly_chart(fig,use_container_width=True)
    #
    # with col2:
    #     revenue=completed["Vehicle Type"]("Booking Values").sum()
    #     fig = px.bar(x=revenue.index,y=revenue.values,orientation="h")
    #     st.plotly_chart(fig,use_container_width=True)

    pie1 ,pie2 =st.columns(2)

    with pie1:
        status=df["Booking Status"].value_counts()
        fig =px.pie(names=status.index,
                    values=status.values)
        st.plotly_chart(fig,use_container_width=True)

