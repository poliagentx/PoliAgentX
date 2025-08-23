# def results(request):
#     if request.method == "POST":
#         param_excel_path = request.session.get('param_excel_path')
#         network_path = request.session.get('network_path')
#         budget_path = request.session.get('budget_file_path')
#         indicators_path = request.session.get('indicators_path')

#         if not all([param_excel_path, network_path, budget_path, indicators_path]):
#             return HttpResponse("Missing required files.", status=400)

#         df_indis = pd.read_excel(indicators_path)
#         N = len(df_indis)
#         I0 = df_indis.I0.values
#         R = df_indis.instrumental
#         qm = df_indis.qm.values
#         rl = df_indis.rl.values
#         indis_index = {code: i for i, code in enumerate(df_indis.indicator_label)}
#         Imax = df_indis.max_value.values
#         Imin = df_indis.min_value.values

#         df_params = pd.read_excel(param_excel_path, skiprows=1)
#         alpha = df_params.alpha.values
#         alpha_prime = df_params.alpha_prime.values
#         betas = df_params.beta.values

#         df_net = pd.read_excel(network_path)
#         A = np.zeros((N, N))
#         for _, row in df_net.iterrows():
#             i = indis_index[row.origin]
#             j = indis_index[row.destination]
#             A[i, j] = row.weight

#         T = int(request.POST.get("num_simulations", 50))

#         df_exp = pd.read_excel(budget_path, sheet_name='template_budget')
#         Bs_retrospective = df_exp.values[:, 1:]
#         Bs = np.tile(Bs_retrospective[:, -1], (T, 1)).T

#         df_rela = pd.read_excel(budget_path, sheet_name='relational_table')
#         B_dict = {
#             indis_index[row.indicator_label]: [p for p in row.values[1:] if pd.notna(p)]
#             for _, row in df_rela.iterrows()
#         }

#         goals = np.random.rand(N) * (Imax - I0) + I0

#         sample_size = 100
#         outputs = []
#         for _ in range(sample_size):
#             output = run_ppi(
#                 I0, alpha, alpha_prime, betas,
#                 A=A, Bs=Bs, B_dict=B_dict, T=T, R=R, qm=qm, rl=rl,
#                 Imax=Imax, Imin=Imin, G=goals
#             )
#             outputs.append(output)

#         tsI, tsC, tsF, tsP, tsS, tsG= zip(*outputs)
#         # tsI_hat shape: (N, T)
#                 # === Step 1: Average across sample runs ===
#         tsI_hat = np.mean(tsI, axis=0)
#         tsC_hat = np.mean(tsC, axis=0)
#         tsF_hat = np.mean(tsF, axis=0)
#         tsP_hat = np.mean(tsP, axis=0)
#         tsS_hat = np.mean(tsS, axis=0)
#         tsG_hat = np.mean(tsG, axis=0)

#         # === Step 2: Helper to build a DataFrame for one set ===
#         def build_df(ts_hat):
#             df_list = []
#             for i, serie in enumerate(ts_hat):
#                 row_dict = {
#                     "indicator_label": df_indis.iloc[i].indicator_label,
#                     "sdg": df_indis.iloc[i].sdg,
#                     "color": df_indis.iloc[i].color,
#                     "goal": goals[i],
#                 }
#                 for t, val in enumerate(serie):
#                     row_dict[str(t)] = val
#                 df_list.append(row_dict)
#             return pd.DataFrame(df_list)

#         # === Step 3: Build DataFrames for each ===
#         df_I = build_df(tsI_hat)
#         df_C = build_df(tsC_hat)
#         df_F = build_df(tsF_hat)
#         df_P = build_df(tsP_hat)
#         df_S = build_df(tsS_hat)
#         df_G = build_df(tsG_hat)

#         # === Step 4: Convert each to JSON ===
#         df_output_json_I = df_I.to_json(orient="records")
#         df_output_json_C = df_C.to_json(orient="records")
#         df_output_json_F = df_F.to_json(orient="records")
#         df_output_json_P = df_P.to_json(orient="records")
#         df_output_json_S = df_S.to_json(orient="records")
#         df_output_json_G = df_G.to_json(orient="records")

#         # === Step 5: Save each DataFrame as a separate Excel file (in memory) ===
#         excel_files = {}
#         for name, df in {
#             "Simulation_I": df_I,
#             "Simulation_C": df_C,
#             "Simulation_F": df_F,
#             "Simulation_P": df_P,
#             "Simulation_S": df_S,
#             "Simulation_G": df_G,
#         }.items():
#             output = BytesIO()
#             with pd.ExcelWriter(output, engine="openpyxl") as writer:
#                 df.to_excel(writer, index=False, sheet_name=name)
#             output.seek(0)
#             excel_files[name] = base64.b64encode(output.getvalue()).decode("utf-8")

#         # Store Excel files in session
#         request.session["excel_files"] = excel_files

#         # === Step 6: Pass everything into context ===
#         context = {
#             "df_output_json_I": df_output_json_I,
#             "df_output_json_C": df_output_json_C,
#             "df_output_json_F": df_output_json_F,
#             "df_output_json_P": df_output_json_P,
#             "df_output_json_S": df_output_json_S,
#             "df_output_json_G": df_output_json_G,
#             "T": T,
#         }
#         return render(request, "results.html", context)

#     return HttpResponse("Please run the simulation first.", status=400)