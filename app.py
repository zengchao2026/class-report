import io
import streamlit as st
import pandas as pd

st.title("班级成绩分析")
st.write("上传一张成绩表，自动算出各项指标。")

uploaded = st.file_uploader("上传成绩表（需要 姓名、班级、分数 三列）", type="xlsx")

if uploaded:
    try:
        df = pd.read_excel(uploaded)
    except Exception as e:
        st.error("这个文件读不出来，请确认它是 xlsx 格式。")
        st.stop()

    if "分数" not in df.columns:
        st.error("表里没有“分数”这一列，请检查表头是不是写对了。")
        st.stop()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("人数", len(df))
    col2.metric("平均分", round(df["分数"].mean(), 1))
    col3.metric("最高分", df["分数"].max())
    col4.metric("最低分", df["分数"].min())

    pass_count = len(df[df["分数"] >= 60])
    pass_rate = round(pass_count / len(df) * 100, 1)
    st.write("及格", pass_count, "人，及格率", str(pass_rate) + "%")

    st.subheader("各班平均分")
    by_class = df.groupby("班级")["分数"].mean().round(1).reset_index()
    st.bar_chart(by_class, x="班级", y="分数", horizontal=True)


    st.subheader("原始数据")
    st.dataframe(df)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as writer:
        df.to_excel(writer, sheet_name="成绩", index=False)
    st.download_button("下载报告", buf.getvalue(), "分析结果.xlsx")
