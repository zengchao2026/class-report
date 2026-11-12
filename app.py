import io
import pandas as pd
import streamlit as st

st.title("班级成绩分析")
st.write("上传成绩表，自动识别是分数版还是等级版。")

uploaded = st.file_uploader("上传成绩表（xlsx）", type="xlsx")

# 各科满分。学校口径变了只改这里
FULL = {
    "语文": 150, "语": 150,
    "数学": 150, "数": 150,
    "英语": 150, "英": 150,
    "政治": 60, "政": 60,
    "历史": 60,
    "物理": 100,
    "化学": 70, "化": 70,
    "地理": 60, "地": 60,
    "生物": 60, "生": 60,
}
ORDER = ["A1", "A2", "B1", "B2", "C1", "C2", "D"]
NOT_SUBJECT = ["班级", "姓名", "名次升降"]

if uploaded:
    try:
        df = pd.read_excel(uploaded)
    except Exception as e:
        st.error("这个文件读不出来，请确认是 xlsx 格式。")
        st.stop()

    if "总分" not in df.columns:
        st.error("表里没有“总分”这一列，请检查表头是不是写对了。")
        st.stop()

    subjects = [c for c in df.columns if c not in NOT_SUBJECT]
    is_score = pd.to_numeric(df["总分"], errors="coerce").notna().mean() > 0.8

    # 只按表里实际有的科目累加满分
    full_total = sum(FULL.get(c, 0) for c in subjects)
    pass_line = full_total * 0.6

    col1, col2, col3 = st.columns(3)
    col1.metric("人数", len(df))

    if is_score:
        df["总分"] = pd.to_numeric(df["总分"])
        for c in subjects:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        col2.metric("平均总分", round(df["总分"].mean(), 1))
        col3.metric("最高总分", df["总分"].max())

        pass_n = int((df["总分"] >= pass_line).sum())
        st.write("总分满分", full_total, "分，及格线", round(pass_line, 1),
                 "分；及格", pass_n, "人，及格率",
                 str(round(pass_n / len(df) * 100, 1)) + "%")

        unknown = [c for c in subjects if c not in FULL]
        if unknown:
            st.warning("这些列的满分没认出来：" + "、".join(unknown) + "，请补进 FULL")

        st.subheader("各科水平（按得分率比较才公平）")
        rows = []
        for c in subjects:
            m = FULL.get(c)
            a = df[c].mean()
            p = int((df[c] >= m * 0.6).sum()) if m else None
            rows.append({
                "科目": c,
                "满分": m or None,
                "平均分": round(a, 1),
                "得分率%": round(a / m * 100, 1) if m else None,
                "及格人数": p,
            })
        tbl = pd.DataFrame(rows)
        st.dataframe(tbl, hide_index=True)

        chart = tbl.dropna(subset=["得分率%"])
        if len(chart):
            st.bar_chart(chart, x="科目", y="得分率%")

        st.subheader("单科明细")
        one = st.selectbox("看哪一科", subjects)
        st.dataframe(df[["姓名", one]].sort_values(one, ascending=False), hide_index=True)
    else:
        col2.metric("总分 A 档人数", int(df["总分"].isin(["A1", "A2"]).sum()))
        col3.metric("总分 D 档人数", int((df["总分"] == "D").sum()))

        st.subheader("总分等级分布")
        dist = df["总分"].value_counts().reindex(ORDER, fill_value=0).reset_index()
        dist.columns = ["等级", "人数"]
        st.bar_chart(dist, x="等级", y="人数")

        st.subheader("单科等级分布")
        one = st.selectbox("看哪一科", subjects)
        d2 = df[one].value_counts().reindex(ORDER, fill_value=0).reset_index()
        d2.columns = ["等级", "人数"]
        st.dataframe(d2, hide_index=True)

    if "名次升降" in df.columns:
        up = pd.to_numeric(df["名次升降"], errors="coerce")
        st.subheader("名次变化")
        st.write("进步", int((up > 0).sum()), "人，退步", int((up < 0).sum()),
                 "人，持平", int((up == 0).sum()), "人")

    st.subheader("原始数据")
    st.dataframe(df, hide_index=True)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf) as writer:
        df.to_excel(writer, sheet_name="成绩", index=False)
    st.download_button("下载原始数据", buf.getvalue(), "成绩明细.xlsx")
