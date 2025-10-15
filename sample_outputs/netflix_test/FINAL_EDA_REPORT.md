## Executive Summary

This Exploratory Data Analysis (EDA) report provides a high-level overview of the content library, highlighting key characteristics and actionable insights. The platform is predominantly a movie-centric service, with a strong emphasis on recent releases, particularly from the United States and India. Dramas and International Movies are the most prevalent genres, catering primarily to a mature audience as indicated by the high proportion of TV-MA and TV-14 ratings. Content duration varies significantly by type, with movies averaging around 104 minutes and TV shows typically represented by single seasons. These findings are crucial for informing content acquisition strategies, audience targeting, and platform development.

## EDA Plan

The following analyses were executed to understand the dataset's key characteristics:

*   Univariate Analysis for type
*   Temporal Trend Analysis for date_added
*   Geographical Distribution Analysis for country
*   Categorical Distribution Analysis for listed_in
*   Categorical Distribution Analysis for rating
*   Comparative Duration Analysis for duration, duration_unit, type

## Key Insights and Visualizations

1.  ![Distribution of type](charts\distribution_of_type.png)
    The platform's content library is heavily skewed towards movies, which constitute 68.0% of all entries. This indicates a primary strategic focus on film content rather than episodic series. This dominance suggests that content acquisition and marketing efforts should primarily cater to movie watchers, while also considering opportunities to strategically grow the TV show segment if diversification is a long-term goal.

2.  ![Temporal Trend - date_added](charts\temporal_trend_date_added.png)
    Analysis of `date_added` reveals significant trends in content acquisition over time. This trend, coupled with the `release_year` statistics (median 2017, mean 2013.62, max 2021, and a strong negative skew of -2.84), clearly indicates a strategic emphasis on recent content. The majority of content added, and indeed released, is from the last decade, suggesting a continuous effort to keep the library fresh and relevant with contemporary titles. This recency bias is crucial for understanding content lifecycle and audience engagement with newer releases.

3.  ![Top 10 country](charts\top_10_country.png)
    The United States and India are the dominant countries contributing content, with the top category (likely United States) accounting for 44.0% of entries. This highlights these two nations as primary content production hubs or key target markets for the platform. This geographical concentration suggests a strategic focus on content appealing to audiences in these regions or leveraging their production capabilities, potentially influencing language availability and cultural themes in the content library.

4.  ![Top 10 listed_in](charts\top_10_listed_in.png)
    Dramas and International Movies are the most prevalent genres, with the top category (likely Dramas) making up 19.7% of all entries. This indicates a strong preference or strategic focus on dramatic storytelling and a significant investment in non-domestic film content. Understanding these popular genres is vital for future content acquisition, ensuring alignment with audience preferences and maintaining a competitive edge in these key categories.

5.  ![Top 10 rating](charts\top_10_rating.png)
    The content library primarily caters to a mature audience, with TV-MA and TV-14 being the most frequent content ratings, together comprising 38.2% for the top category (likely TV-MA). This suggests that a substantial portion of the platform's offerings is intended for adult and young adult viewers, implying a need for content guidelines and marketing efforts tailored to this demographic. Content for younger audiences appears to be less emphasized.

6.  ![Duration by type](charts\duration_by_type.png)
    Content duration varies significantly by type. Movies have a median duration of 104 minutes, aligning with typical feature film lengths. In contrast, TV shows have a median duration of 1, which likely represents the number of seasons rather than individual episode lengths. The overall `duration` statistics (median 94.0, mean 73.82) are influenced by this bimodal distribution, with the longer movies pulling the overall median up, while the representation of TV shows as '1 season' contributes to the lower overall mean when considering all entries. This distinction is critical for understanding content consumption patterns and optimizing playback experiences for different content formats.

## Conclusion

This EDA reveals a platform heavily invested in recent movie content, primarily sourced from the US and India, with a strong leaning towards dramas and international films for a mature audience. The distinct duration profiles for movies and TV shows underscore the need for tailored content strategies. These insights provide a robust foundation for strategic decision-making in content acquisition, audience targeting, and platform development, ensuring alignment with current content strengths and market opportunities.

---

**NOTE:** All charts are generated and saved as separate PNG files in the `./charts/` directory. The report refers to them by their title (e.g., ![Gender Distribution](charts/gender_distribution.png)).