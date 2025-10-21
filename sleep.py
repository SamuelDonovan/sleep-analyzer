import datetime
import glob
import pandas as pd
import plotly.graph_objects as go

TARGET_SLEEP = 8


def assign_sleep_day(bedtime: datetime.datetime, cutoff_hour: int = 4) -> datetime.date:
    """Converts date to previous day if bedtime is between midnight and a
    specfied cutoff.

     Parameters
    ----------
    bedtime : datetime.datetime
        Time that sleep started, including after midnight.
    cutoff_hour : int
        The hour from midnight to count as the previous night.

    Returns
    -------
    datetime.date
        Date corrected for nights that sleep started after midnight."""
    if 0 <= bedtime.hour < cutoff_hour:
        return (bedtime - datetime.timedelta(days=1)).date()
    else:
        return bedtime.date()


def augment_data(df: pd.DataFrame) -> pd.DataFrame:
    """Adds additional data to the provided dataframe such as:
    * date
    ** The date that sleep started.
    * sleep_hours
    ** The number of hours slept for the night.
    * sleep_delta
    ** The number of hours off of the sleep target.
    * cumulative_debt_burnup
    ** The cumulative sleep delta.
    * rolling_14d_debt
    ** A 14 day rolling sum of the sleep delta.
    * rolling_7d_sleep
    ** A 7 day rolling average of the numbers of hour slept.
    * color
    ** A color to specify if the sleep is above or below the sleep target.

    Parameters
    ----------
    df: pd.DataFrame
        The data to augement.

    Returns
    -------
    pd.DataFrame
        The dataframe with additional helpful data added."""
    # Format must be mixed as the seconds field is dropped from the dataset
    # if zero.
    df["date"] = pd.to_datetime(df["Start Time"], format="mixed")
    df["date"] = df["date"].apply(assign_sleep_day)
    df["sleep_hours"] = df["Time Asleep(min)"] / 60

    # Sum all sleep periods per day such that naps are inlcuded.
    df = df.groupby("date", as_index=False)["sleep_hours"].sum()

    df["Sleep Delta"] = df["sleep_hours"] - TARGET_SLEEP
    df["rolling_14d_debt"] = (-df["Sleep Delta"]).rolling(14, min_periods=1).sum()
    # A simple marker indicating if the sleep goal was met.
    df["color"] = df["sleep_hours"].apply(
        lambda x: "lightcoral" if x < TARGET_SLEEP else "lightgreen"
    )
    df["rolling_7d_sleep"] = df["sleep_hours"].rolling(7, min_periods=1).mean()
    return df


def get_file(extension: str) -> str:
    """Return the first file in the current directory with specified file extension.

    Parameters
    ----------
    extension : str
        The file extension to search for.

    Returns
    -------
    str
        The first file found with the specified extension."""
    return glob.glob(f"*.{extension}")[0]


def plot_sleep_data(df: pd.DataFrame) -> None:
    """Plots sleep data.

    Parameters
    ----------
    df : pd.DataFrame
        The data to plot.

    Returns
    -------
    None"""
    fig = go.Figure()

    # Nightly sleep bars
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["sleep_hours"],
            marker_color=df["color"],
            name="Sleep Hours",
        )
    )

    # Target & average lines
    fig.add_hline(
        y=TARGET_SLEEP, line_dash="dash", line_color="orange", name="Target Sleep"
    )

    # 7-day rolling average sleep
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["rolling_7d_sleep"],
            mode="lines",
            line=dict(color="blue", width=2),
            name="7-Day Avg Sleep",
        )
    )

    # 14-day rolling debt
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["rolling_14d_debt"],
            mode="lines",
            line=dict(color="purple", width=2),
            name="14-Day Debt Window",
        )
    )

    fig.update_layout(
        title="Sleep Debt Overview",
        xaxis_title="Date",
        yaxis_title="Hours",
        yaxis2=dict(title="Sleep Debt (Hours)", overlaying="y", side="right"),
        template="plotly_white",
        bargap=0.2,
    )

    fig.show()


if __name__ == "__main__":
    first_csv_file_found = get_file("csv")
    df = pd.read_csv(first_csv_file_found)
    df = augment_data(df)
    plot_sleep_data(df)
