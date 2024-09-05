                    # html.Div(
                    #     [                    
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        subnav_academic_information(),
                                                        id="subnav-academic-info",
                                                        className="tabs",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
                                            ),
                                        ],
                                        className="row",
                                    ),
                                ],
                                id="academic-information-subnav-container",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        subnav_academic_analysis(),
                                                        id="subnav-academic-analysis",
                                                        className="tabs",
                                                    ),
                                                ],
                                                className="bare-container--flex--center twelve columns",
                                            ),
                                        ],
                                        className="row",
                                    ),
                                ],
                                id="academic-analysis-subnav-container",
                            ),

                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "academic", "type"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),


                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "academic-information", "category"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                          
                    #     ],
                    #     id="academic-information-navigation-container",
                    # ),
                 
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "analysis-multi", "hs-group"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                                  
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "analysis-multi", "subject", "six"
                                                ),
                                                className="tabs",
                                            ),
                                            html.Div(
                                                create_radio_layout(
                                                    "analysis-multi", "category", "six"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center_subnav twelve columns",
                                    ),
                                ],
                                className="row",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                create_radio_layout(
                                                    "analysis-multi", "subcategory"
                                                ),
                                                className="tabs",
                                            ),
                                        ],
                                        className="bare-container--flex--center twelve columns",
                                    ),
                                ],
                                className="row",
                            ),