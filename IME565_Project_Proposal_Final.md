# Beyond Wrapped: A Multi-Phase Spotify Analytics Platform with Predictive Insights

**IME 565: Predictive Data Analytics for Engineers**  
**Fall Quarter 2025**

**Team Members:** Nicolo DiFerdinando, Joe Mascher, Rithvik Shetty  
**Date:** October 30, 2025

---

## Abstract
`
While Spotify's annual "Wrapped" feature generates 425 million social media engagements and serves 156 million users, it provides only surface-level retrospective summaries of listening habits without predictive capabilities or actionable insights. This project aims to develop a comprehensive, multi-phase music analytics platform that addresses critical gaps in existing tools: lack of playlist intelligence, absence of contextual listening analysis, and failure to provide ongoing utility beyond annual novelty. 

By leveraging Spotify's API data combined with publicly available datasets containing audio features (tempo, energy, valence, danceability, acousticness), listening timestamps, and track metadata, we will build machine learning models that predict future preferences, identify temporal patterns, and provide personalized recommendations. Our phased approach ensures deliverable milestones within course constraints while maintaining ambitious long-term goals. Phase 1 establishes foundational analytics using public datasets, Phase 2 adds sophisticated playlist intelligence, and Phase 3 implements predictive modeling and contextual awareness. This tool will offer users deeper understanding of their musical journey, actionable insights for music discovery, and explanations of the "why" behind their listening habits—delivering sustained engagement rather than one-time viral appeal.

---

## Problem Description

Current music analytics tools fall into three categories, each with critical shortcomings:

**1. Limited Depth (Spotify Wrapped)**  
Spotify's Wrapped provides top songs, artists, and genres but lacks insight into *why* users gravitate toward certain music, how tastes evolve over time, or what listening patterns reveal about daily routines and emotional states. Research demonstrates that music listening is strongly correlated with mood, time of day, and activity type, yet users currently have no way to visualize these patterns or understand the audio characteristics that define their preferences.

**2. Unreliable Execution (Stats.fm)**  
Stats.fm offers the most comprehensive feature set with 15 million users but suffers from critical execution flaws. Users consistently report buggy performance with features failing to load 40% of the time, disconnected UI/UX where features feel like "spaghetti thrown at a wall," and inaccurate genre categorization. The technical approach requires manual Spotify data export uploads, creating significant friction in user onboarding.

**3. One-Time Novelty (Obscurify)**  
Obscurify succeeds at generating viral social media sharing through "obscurity ratings" comparing users against 120+ million Spotify listeners. However, users report it as "fun to check once" with zero long-term value or reason to revisit. The tool demonstrates that shareability creates awareness but doesn't build sustainable engagement.

### Research-Identified Gaps

Academic research on music recommender systems identifies six critical challenges our project addresses:

1. **Lack of Transparency and Explanations**: Existing recommendation algorithms work as "black boxes"—users receive suggestions but don't understand the reasoning behind them
2. **Limited Context-Awareness**: Current tools don't separate listening contexts (work focus music vs. workout energy vs. sleep background noise), contaminating recommendations and analytics
3. **Absence of Temporal Intelligence**: Most tools provide static snapshots rather than revealing how preferences evolve across weekly, monthly, and seasonal cycles
4. **Missing Playlist Intelligence**: Despite playlists being the primary music organization method, no tool offers health metrics, overlap detection, or optimization suggestions
5. **Gap Between Accuracy and User Value**: High prediction accuracy doesn't necessarily translate to user satisfaction; meaningful insights require connecting to identity, emotional awareness, and discovery guidance

### The Opportunity

Music listening data reveals profound insights about temporal patterns, emotional states, and personal identity. Research analyzing 1.5 years of streaming data (Marey et al., 2024) demonstrates that distinct patterns emerge with weekday morning peaks for commuting, working hours concentration for focus listening, and weekend evening peaks for social contexts. Linear prediction models achieve R² of 0.75 for energy/arousal and 0.59 for emotional valence from audio features alone (Brinker et al., 2012). 

**Our project will empower users to:**
- Understand *when* they listen to *what* through temporal pattern analysis
- Identify the audio characteristics (energy, valence, tempo, acousticness) that define their taste
- Track mood trajectories across days, weeks, and months
- Optimize playlist organization and eliminate redundancies
- Discover new music aligned with evolving preferences through explainable recommendations
- Separate listening contexts to prevent algorithmic contamination

This addresses the fundamental question of why 15 million users tolerate buggy software and why viral success doesn't translate to retention: users desperately want analytics providing ongoing utility through actionable intelligence rather than backward-looking vanity metrics.

---

## Summary of Data

Our multi-phase approach leverages different data sources appropriate to each development stage:

### Phase 1: Public Datasets (Foundation)

We will utilize publicly available Spotify datasets from Kaggle to establish our analytical foundation and machine learning pipelines:

- **Spotify Tracks Dataset** (~114,000 tracks): Comprehensive audio features for a diverse music collection including danceability, energy, key, loudness, mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration, and time signature
- **Top Spotify Songs datasets** (2023, 2020-2023 compilations): 50,000-170,000 tracks with popularity metrics, release dates, and streaming statistics
- **Million Song Dataset subset**: Academic benchmark dataset providing additional validation data for model training

### Phase 2 & 3: User Data Integration (Advanced)

For personalized analytics and predictions, users can optionally provide:

- **Spotify API Recent History**: Last 50 tracks via API's recently-played endpoint
- **Privacy Export Data** (optional): Users can request complete listening history from Spotify (received as JSON files within 3-30 days), containing timestamp, track, artist, album, platform, duration played, and listening session metadata

Heavy users accumulate 120,000-174,000 streaming events over multiple years, representing substantial temporal depth for pattern analysis.

### Data Structure and Features

Our primary analytical features include:

| Feature Category | Specific Metrics | Description |
|-----------------|------------------|-------------|
| **Audio Features** | danceability, energy, valence, tempo, acousticness, instrumentalness, speechiness, liveness | Spotify's machine-generated audio analysis (0.0-1.0 scale for most) |
| **Temporal Data** | played_at timestamp, day of week, hour of day, season | When tracks are played, enabling circadian and seasonal analysis |
| **Track Metadata** | track_id, track_name, artist_name, album_name, duration_ms, popularity, genre | Identifying and categorizing music |
| **User Context** | playlist source, shuffle state, skip behavior | Understanding listening intent and engagement |

### Feature Engineering Opportunities

Research demonstrates that composite features improve prediction while maintaining interpretability:

- **Mood Score**: Combining valence (emotional positivity), energy (intensity), and acousticness to create overall emotional profiles
- **Grooviness Index**: Merging danceability, energy, and tempo to identify upbeat, movement-oriented music
- **Focus Suitability**: Weighting low speechiness, moderate energy, and high instrumentalness for concentration activities
- **Temporal Patterns**: Aggregating by hour-of-day, day-of-week, and season to reveal contextual preferences

---

## Project Plan with Timeline

### Three-Phase Development Strategy

Our approach balances ambitious goals with realistic 10-week course constraints by establishing clear phase boundaries. Each phase delivers standalone value, ensuring meaningful deliverables even if time limitations prevent completing all phases.

### **Phase 1: Foundation Analytics** (Weeks 6-7)
*Goal: Establish core visualization and analysis pipeline using public datasets*

**Week 6 (Oct 27 - Nov 2)**
- Set up development environment and project repository
- Acquire and explore public Kaggle datasets (114k+ tracks with audio features)
- Data cleaning and preprocessing pipeline development
- Exploratory data analysis in Jupyter notebooks
- Initial statistical summaries and distribution visualizations

**Week 7 (Nov 3-9)**
- Implement core visualization components:
  - Temporal analysis (listening by hour, day, week, month)
  - Audio feature distributions and correlations
  - Top tracks/artists/genres identification
  - Genre evolution over time
- Create interactive dashboard framework (Streamlit)
- Begin documentation of methodology and findings

**Phase 1 Deliverable**: Interactive analytics dashboard displaying comprehensive listening statistics, temporal patterns, and audio feature analysis using public dataset as proof-of-concept. This standalone deliverable demonstrates technical competency and analytical sophistication suitable for course completion.

---

### **Phase 2: Playlist Intelligence** (Week 8-9, if time permits)
*Goal: Add sophisticated playlist analytics addressing unmet user needs*

**Week 8 (Nov 10-16) - Midterm Week**
- Design playlist analysis algorithms:
  - Health metrics (save-to-play ratio, recency scores)
  - Overlap detection across multiple playlists
  - Freshness analysis based on listening patterns
- Implement playlist optimization recommendations
- Continue work alongside midterm exam preparation

**Week 9 (Nov 17-23) - Thanksgiving Week**
- Complete playlist intelligence features
- User interface for playlist comparison and management
- Integration testing with Phase 1 foundation
- Prepare visualizations for playlist insights

**Phase 2 Deliverable**: Enhanced platform with playlist intelligence features providing actionable recommendations for playlist organization, redundancy elimination, and optimization—addressing a critical gap no competitor currently fills.

---

### **Phase 3: Predictive Modeling & Context Awareness** (Week 10+, stretch goal)
*Goal: Implement machine learning predictions and contextual analytics*

**Week 10 (Nov 24-30 / Dec 1-4)**
- Feature engineering for machine learning (composite scores, temporal features)
- Train ensemble models for preference prediction:
  - Random Forest baseline (target: 74-77% accuracy)
  - XGBoost implementation (target: 70-75% accuracy)
  - Voting ensemble combining multiple classifiers
- Implement context detection through clustering:
  - Automatic activity classification (workout, focus, relaxation)
  - Time-of-day pattern recognition
  - Mood trajectory tracking
- Model evaluation and hyperparameter tuning
- Integration of predictions into dashboard UI
- Finalize presentation materials

**Phase 3 Deliverable**: Complete platform with predictive capabilities for music preference forecasting, automated context detection, personalized recommendations with explanations, and mood trajectory visualization—delivering the full vision of actionable, ongoing-utility analytics.

---

### Final Deliverables (All Phases)

**Project Proposal (5%)**: Due Thu, Oct 30 (Week 6) ✓  
**Project Presentation (25%)**: Tue, Dec 2 & Thu, Dec 4 (Week 10)  
- 12-15 minute presentation covering:
  - Problem motivation and research-identified gaps
  - Data sources and preprocessing methodology
  - Analytical techniques and visualizations
  - Machine learning models and performance (if Phase 3 completed)
  - Key insights and user value proposition
  - Demonstration of interactive dashboard
  - Future development roadmap

**Phase-Dependent Success Criteria:**
- **Minimum Viable (Phase 1)**: Comprehensive analytics dashboard with public data demonstrating temporal analysis, audio feature insights, and top content identification
- **Target (Phase 1-2)**: Above plus sophisticated playlist intelligence with health metrics and optimization recommendations
- **Aspirational (Phase 1-3)**: Complete platform with predictive modeling, context detection, and personalized recommendation engine

---

## Methodology and Technical Approach

### Data Processing Pipeline

1. **Data Acquisition**: Load public Kaggle datasets with 114k-170k tracks and comprehensive audio features
2. **Preprocessing**: 
   - Handle missing values (audio features occasionally null for deleted content)
   - Remove duplicates and invalid entries (loudness values > 0 dB violate specifications)
   - Filter noise (plays under 5 seconds indicate skipping rather than listening)
   - Normalize features to [0,1] scale using MinMaxScaler
3. **Feature Engineering**: Create composite metrics (mood scores, grooviness indices, context suitability scores)
4. **Aggregation**: Generate temporal summaries by hour-of-day, day-of-week, and seasonal patterns

### Machine Learning Approach (Phase 3)

Research demonstrates ensemble methods consistently outperform single-model approaches for music preference prediction:

**Model Architecture:**
- **Random Forest Classifier**: Baseline model achieving 74-77% accuracy across multiple studies
- **XGBoost**: Gradient boosting achieving 70-75% accuracy, dominates Kaggle competitions
- **Ensemble Voting System**: Combine Random Forest, XGBoost, SVM, and K-Neighbors for 80-85% accuracy
- **Content-Based Fallback**: Use audio feature similarity for cold-start scenarios (new tracks without interaction data)

**Key Features for Prediction:**
- Audio characteristics: energy, speechiness, acousticness, danceability, valence
- Temporal patterns: hour-of-day preferences, day-of-week trends
- Historical behavior: genre distributions, artist preferences, skip patterns
- Context indicators: playlist sources, session duration, shuffle behavior

**Validation Strategy:**
- 80/20 train-test split with stratification by genre
- Cross-validation for hyperparameter tuning
- Evaluation metrics: accuracy, precision, recall, F1-score, and confusion matrices
- Interpretability analysis: feature importance rankings, SHAP values for explainability

### Visualization Strategy

Interactive dashboards will employ:
- **Temporal Line Charts**: Listening patterns across time with zoom/pan capabilities
- **Radar/Spider Charts**: Audio feature profiles comparing tracks, artists, or time periods
- **Histograms**: Distribution analysis for tempo, energy, and popularity
- **Scatter Plots**: Genre evolution and audio feature relationships
- **Heatmaps**: Hour-of-day × day-of-week listening intensity patterns
- **Network Graphs**: Artist and genre relationship mapping

All visualizations will prioritize interpretability and actionability over complexity, ensuring users gain meaningful insights without requiring technical expertise.

---

## Expected Outcomes and Value Proposition

### For Users (Personal Value)

1. **Temporal Intelligence**: Understand when they naturally prefer certain music types, optimizing playlists for specific times/activities
2. **Playlist Optimization**: Identify dead playlists, eliminate redundancies, and improve organization efficiency
3. **Discovery Guidance**: Receive explainable recommendations aligned with evolving taste, not black-box algorithms
4. **Mood Awareness**: Track emotional patterns through valence and energy analysis, promoting self-reflection
5. **Ongoing Utility**: Weekly/monthly insights providing sustained engagement versus one-time annual summary

### For Our Team (Learning Objectives)

1. **Advanced Data Engineering**: Processing 100k+ track datasets with complex temporal and audio feature data
2. **Machine Learning Pipeline**: End-to-end implementation from feature engineering through model deployment
3. **User-Centered Analytics**: Translating statistical findings into actionable, non-technical insights
4. **Interactive Dashboard Development**: Building production-quality web applications for data visualization
5. **Research Integration**: Applying academic findings on music information retrieval to practical applications

### Differentiation from Existing Tools

| Feature | Stats.fm | Obscurify | Spotify Wrapped | **Our Platform** |
|---------|----------|-----------|-----------------|------------------|
| Temporal Pattern Analysis | Limited | None | Annual only | ✓ Deep weekly/monthly |
| Playlist Intelligence | Basic stats | None | None | ✓ Health metrics & optimization |
| Context Separation | None | None | None | ✓ Activity detection |
| Predictive Recommendations | Basic | None | None | ✓ With explanations |
| Ongoing Utility | High friction | One-time | Annual | ✓ Weekly engagement |
| Execution Quality | Buggy | Good | Excellent | ✓ Target: Excellent |

---

## Risk Mitigation and Contingencies

### Technical Risks

**Risk**: Insufficient time to complete all three phases  
**Mitigation**: Phased approach with standalone deliverables at each stage; Phase 1 alone satisfies course requirements

**Risk**: Dataset limitations (public data lacks personal temporal patterns)  
**Mitigation**: Demonstrate methodology with public data; document how personal data integration would enhance analysis

**Risk**: Machine learning model underperformance  
**Mitigation**: Well-researched baseline models (Random Forest) provide 74-77% accuracy floor; ensemble approach offers improvement path

### Data Risks

**Risk**: Public datasets missing critical features  
**Mitigation**: Multiple Kaggle datasets identified (114k-170k tracks); worst case, use Million Song Dataset subset as academic benchmark

**Risk**: Data quality issues (missing values, outliers)  
**Mitigation**: Comprehensive preprocessing pipeline based on research-identified common issues; explicit handling strategies for each data problem type

### Scope Risks

**Risk**: Feature creep preventing completion  
**Mitigation**: Clear phase boundaries with defined success criteria; prioritize Phase 1 completion above all else

---

## Academic Foundation and Citations

This project builds on established research in music information retrieval, recommendation systems, and user engagement:

**Temporal Pattern Analysis:**
- Marey, E., Sguerra, B., & Moussallam, M. (2024). Modeling Activity-Driven Music Listening with PACE. *ACM SIGIR Conference on Research and Development in Information Retrieval*. Demonstrates quantitative frameworks for circadian and weekly listening cycles, achieving ROC AUC scores of 0.56-0.73 predicting different activities.

**Audio Features and Emotion:**
- Brinker, B., van Dinther, R., & Skowronek, J. (2012). Expressed music mood classification compared with valence and arousal ratings. *EURASIP Journal on Audio, Speech, and Music Processing*, 24. Establishes valence-arousal as primary emotional dimensions with R² of 0.75 for arousal and 0.59 for valence prediction from audio features.

**Music Recommendation Challenges:**
- Schedl, M., Zamani, H., Chen, C. W., Deldjoo, Y., & Elahi, M. (2018). Current challenges and visions in music recommender systems research. *International Journal of Multimedia Information Retrieval*, 7(2), 95-116. Comprehensive survey identifying transparency, context-awareness, and beyond-accuracy evaluation as critical gaps.

**User Engagement with Music Analytics:**
- Miller, M., Martinson, M., Bueckert, R., et al. (2022). Augmenting Digital Sheet Music through Visual Analytics. *Computer Graphics Forum*, 41(3), 451-462. Demonstrates that visual analytics increase insight generation and willingness to explore musical data.

**Machine Learning for Music:**
- Multiple studies on Kaggle and in peer-reviewed venues demonstrate Random Forest (74-77% accuracy) and XGBoost (70-75% accuracy) as reliable baselines for Spotify audio features classification, with ensemble methods reaching 80-85% accuracy.

---

## Conclusion

This project addresses a clear market need: the 15 million users tolerating stats.fm's buggy software and Obscurify's one-time novelty demonstrate massive demand for music analytics that provide ongoing utility. Our research-backed, multi-phase approach ensures deliverable value at each stage while pursuing an ambitious vision of actionable, explainable, context-aware music intelligence.

By combining foundational analytics with playlist intelligence and predictive modeling, we will create a tool addressing gaps that all existing competitors fail to solve. The phased structure provides realistic scope management for the 10-week course timeline while maintaining goals ambitious enough to deliver a tool our team will continue using and developing beyond semester completion.

Most importantly, we're not building another clone of existing tools—we're answering the fundamental question: **What if music analytics provided the ongoing utility of a personal music coach rather than the one-time entertainment of a social media filter?** This project delivers exactly that.

---

## References

[1] Marey, E., Sguerra, B., & Moussallam, M. (2024). Modeling Activity-Driven Music Listening with PACE. *ACM SIGIR Conference on Research and Development in Information Retrieval*. https://arxiv.org/html/2405.01417

[2] Brinker, B., van Dinther, R., & Skowronek, J. (2012). Expressed music mood classification compared with valence and arousal ratings. *EURASIP Journal on Audio, Speech, and Music Processing*, 24. https://asmp-eurasipjournals.springeropen.com/articles/10.1186/1687-4722-2012-24

[3] Schedl, M., Zamani, H., Chen, C. W., Deldjoo, Y., & Elahi, M. (2018). Current challenges and visions in music recommender systems research. *International Journal of Multimedia Information Retrieval*, 7(2), 95-116.

[4] Miller, M., Martinson, M., Bueckert, R., Garth, C., & Bruckner, S. (2022). Augmenting Digital Sheet Music through Visual Analytics. *Computer Graphics Forum*, 41(3), 451-462.

[5] Spotify for Developers. (2024). Web API Reference. Retrieved from https://developer.spotify.com/documentation/web-api

[6] Multiple Kaggle Datasets. Spotify Tracks Dataset (114k+ tracks), Top Spotify Songs 2023 (170k+ tracks), with comprehensive audio feature data. Retrieved from https://www.kaggle.com/

[7] Business of Apps. (2024). Spotify Wrapped Statistics and User Engagement. Retrieved from https://www.businessofapps.com/data/spotify-statistics/