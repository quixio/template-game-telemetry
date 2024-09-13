```mermaid
%%{ init: { 'flowchart': { 'curve': 'monotoneX' } } }%%
graph LR;
Game_Telemetry_WS[fa:fa-rocket Game Telemetry WS &#8205] --> clickstream{{ fa:fa-arrow-right-arrow-left clickstream &#8205}}:::topic;
Snake_game[fa:fa-rocket Snake game &#8205]
clickstream{{ fa:fa-arrow-right-arrow-left clickstream &#8205}}:::topic --> s3-sink[fa:fa-rocket s3-sink &#8205];


classDef default font-size:110%;
classDef topic font-size:80%;
classDef topic fill:#3E89B3;
classDef topic stroke:#3E89B3;
classDef topic color:white;
```