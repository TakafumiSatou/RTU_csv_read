# -*- coding: utf_8 -*-
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib import rcParams
import io
import os

rcParams['font.family'] = 'Meiryo'

st.markdown("""
    <style>
        html, body {
            overflow: auto !important;
        }
        .main {
            overflow: auto !important;
        }
        .block-container {
            padding-bottom: 100px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("RTU用 作業時間分析アプリ", layout="wide")

# CSVファイルのアップロード
uploaded_csv = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

# 画像ファイルのアップロード（複数可）
uploaded_images = st.file_uploader("画像ファイルをアップロードしてください（複数選択可）", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# 画像ファイル名とバイナリを辞書に保存（拡張子を除いたキーで保存）
image_dict = {}
if uploaded_images:
    for img in uploaded_images:
        base_name = os.path.splitext(img.name)[0].lower()
        image_dict[base_name] = img

# CSVの処理
if uploaded_csv is not None:
    df = pd.read_csv(uploaded_csv, encoding="cp932", on_bad_lines="skip")

    if set(["日時", "ファイル名", "判定結果"]).issubset(df.columns):
        df = df[["日時", "ファイル名", "判定結果"]]
        df["日時"] = pd.to_datetime(df["日時"], errors="ignore")
        df = df.sort_values("日時").reset_index(drop=True)
        df.insert(df.columns.get_loc("ファイル名")+1, "Time", df["日時"].diff().dt.total_seconds())

        st.write("### データテーブル")
        st.dataframe(df, use_container_width=True)

        # 行選択：ファイル名を選ぶ
        selected_row = st.selectbox("画像を表示する行を選んでください", df.index)
        selected_file = df.loc[selected_row, "ファイル名"]
        match_key = os.path.splitext(selected_file)[0].lower()

        # 柔軟なマッチング
        matched_img = None
        for key in image_dict:
            if match_key in key:
                matched_img = image_dict[key]
                break

        if matched_img:
            st.image(matched_img, caption=selected_file, use_container_width=True)
        else:
            st.warning(f"画像が見つかりません: {selected_file}")

        # セッションに保存
        st.session_state["df"] = df
    else:
        st.error("CSVに必要な列（日時、ファイル名、判定結果）が含まれていません。")
else:
    st.warning("CSVファイルをアップロードしてください。")


# -------------------------
# セッションからdfと画像を利用
# -------------------------
if "df" in st.session_state:
    df = st.session_state["df"]
    
    def plot_graph():
        column = "Time"
        bins = st.slider("ビンの数 (棒の数)", min_value=5, max_value=100, value=50)

        min_val = int(df[column].min())
        max_val = int(df[column].max())
        range_values = st.slider(
            "表示する数値の範囲",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val),
            step=1
        )
        lower, upper = range_values
        filtered_data = df[(df[column] >= lower) & (df[column] <= upper)][column]

        fig, ax = plt.subplots()
        ax.hist(filtered_data, bins=bins, color="skyblue", edgecolor="black")
        ax.set_title(f"{column} hist")
        ax.set_xlabel(column + " (sec)")
        ax.set_ylabel("count")
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

        if st.button("平均値と中央値を計算"):
            mean_val = filtered_data.mean()
            median_val = filtered_data.median()

            text_str = f"mean: {mean_val:.2f} sec\nmedian: {median_val:.2f} sec"
            ax.text(
                0.95, 0.95, text_str,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="gray")
            )

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)

            st.download_button(
                label="グラフをダウンロード",
                data=buf,
                file_name="histogram_with_stats.png",
                mime="image/png"
            )

        st.pyplot(fig)

    if st.button("ヒストグラムを表示"):
        st.session_state["show_graph"] = True

    if st.session_state.get("show_graph", False):
        plot_graph()
else:
    st.warning("CSVファイルをアップロードしてください。")





