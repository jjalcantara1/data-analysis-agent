## Executive Summary

This Exploratory Data Analysis (EDA) report provides a concise overview of a content platform's library, comprising 149,512 records. Key findings indicate a strong dominance of movies (68%) over TV shows, with a significant portion of content added in recent years, particularly peaking around 2019-2020. The platform's content acquisition is heavily focused on the United States and India, with "Dramas" and "International Movies" being the most prevalent genres. The content skews towards mature audiences, with "TV-MA" and "TV-14" ratings being most common. Analysis of content duration reveals typical movie lengths around 104 minutes, while TV shows are primarily represented by single-unit durations, likely indicating seasons or episodes. The content library shows a strong recency bias, with a median release year of 2017, despite content dating back to 1925.

## EDA Plan

The following analyses were executed to understand the dataset's characteristics:

*   Univariate Analysis for `type`
*   Temporal Trend Analysis for `date_added`
*   Geographical Distribution Analysis for `country`
*   Categorical Distribution Analysis for `listed_in`
*   Categorical Distribution Analysis for `rating`
*   Comparative Duration Analysis for `duration`, `duration_unit`, `type`

## Key Insights and Visualizations

1.  ![Distribution of type](charts\distribution_of_type.png)
    The platform's content library is predominantly composed of Movies, accounting for 68.0% of all entries. This significant imbalance suggests a primary focus on film content, potentially catering to audiences who prefer standalone viewing experiences. While TV Shows make up the remaining 32.0%, the platform's strategy appears to prioritize a movie-centric catalog, which could influence content acquisition, marketing efforts, and subscriber engagement strategies. Understanding this distribution is fundamental to assessing the platform's core offering.

2.  ![Temporal Trend - date_added](charts\temporal_trend_date_added.png)
    Analysis of content addition over time reveals a clear upward trend, with a notable surge in content added around 2019 and 2020. This indicates a period of aggressive content expansion and acquisition by the platform. The strong negative skew (-2.84) in `release_year` statistics, with a median release year of 2017 compared to a mean of 2013.62, further supports the observation that the platform has been actively adding more recent content, despite having a long tail of older titles dating back to 1925. This recent content push suggests a strategy to keep the library fresh and relevant to contemporary audiences.

3.  ![Top 10 country](charts\top_10_country.png)
    The geographical distribution of content highlights a strong concentration from the United States and India, which together represent a substantial portion of the platform's library. The United States alone accounts for 44.0% of the top category, underscoring its role as a primary content source and target market. This focus suggests a strategic emphasis on these regions for content production, licensing, and audience engagement, potentially indicating a localized content strategy or strong market penetration in these countries.

4.  ![Top 10 listed_in](charts\top_10_listed_in.png)
    The most prevalent content categories are "Dramas" and "International Movies," with "Dramas" leading the list. This indicates a strong preference or strategic focus on dramatic storytelling and a significant investment in non-domestic film content. The high ranking of "International Movies" aligns with the substantial content contribution from countries like India, suggesting a diverse global film catalog within the drama genre. This focus helps define the platform's content identity and target audience preferences.

5.  ![Top 10 rating](charts\top_10_rating.png)
    The content ratings are heavily skewed towards mature audiences, with "TV-MA" and "TV-14" being the most frequent ratings, together comprising 38.2% of the top category. "TV-MA" (Mature Audience) indicates content suitable for adults, while "TV-14" (Parents Strongly Cautioned) is for viewers 14 and older. This distribution suggests that the platform primarily targets adult and young adult demographics, with less emphasis on content suitable for younger children. This insight is crucial for understanding the platform's target demographic and content suitability guidelines.

6.  ![Duration by type](charts\duration_by_type.png)
    A comparative analysis of content duration reveals distinct patterns for Movies and TV Shows. The median duration for Movies is 104.00 minutes, which aligns well with typical feature film lengths. In contrast, the median duration for TV Shows is 1.00, which likely represents the number of seasons or episodes rather than runtime, given the nature of TV series. The overall `duration` statistics show a mean of 73.82 and a median of 94.0, with a slight negative skew (-0.27). The wide range (1 to 312) and the difference between mean and median are influenced by the high volume of short TV show entries and the longer movie durations. This distinction is critical for understanding content consumption patterns and library structure.

## Conclusion

The EDA reveals a content platform heavily invested in movies, particularly dramas and international films, with a strong focus on recent content additions from the United States and India. The library primarily caters to adult and young adult audiences, as evidenced by the dominant TV-MA and TV-14 ratings. While movies typically offer standard feature lengths, TV shows are structured differently, likely by season or episode count. These insights provide a foundational understanding of the platform's content strategy, target audience, and library composition, which can inform future content acquisition, marketing, and user experience enhancements. Further analysis could delve into the performance of specific genres, the impact of content age on viewership, and the correlation between cast members and content popularity.

---

**NOTE:** All charts are generated and saved as separate PNG files in the `./charts/` directory. The report refers to them by their title (e.g., ![Gender Distribution](charts/gender_distribution.png)).