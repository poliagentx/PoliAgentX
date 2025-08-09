import pandas as pd

def expand_budget(data_exp):
    years = [col for col in data_exp.columns if str(col).isdigit()]
    periods = len(years)
    T = 1 * periods
    t = int(T / periods)
    new_rows = []
    for _, row in data_exp.iterrows():
        new_row = [row.sdg]
        for year in years:
            new_row += [int(row[year]) for _ in range(t)]
        new_rows.append(new_row)
    return pd.DataFrame(new_rows, columns=['sdg'] + list(range(T)))

# def budgets_page(request):
#     indicators_path = request.session.get('indicators_path')
#     if not indicators_path:
#         messages.error(request, "Indicators file is missing. Please upload it first.")
#         return redirect('upload_indicators')

#     allocation = get_sdg_allocation_from_file(indicators_path)
#     budget_form = BudgetForm()
#     upload_form = Uploaded_Budget()

#     if request.method == 'POST':
#         data_exp = None

#         # Handle manual budget input
#         if 'process_budget' in request.POST:
#             budget_form = BudgetForm(request.POST)
#             if budget_form.is_valid():
#                 budget = budget_form.cleaned_data['budget']
#                 inflation = budget_form.cleaned_data['inflation_rate']
#                 adjusted_budget = budget / (1 + (inflation / 100))
#                 data_indi = pd.read_excel(indicators_path)

#                 # Generate yearly data for each SDG
#                 years = sorted([int(col) for col in data_indi.columns if str(col).isdigit()])

#                 periods = len(years) # Default number of years
#                 data_exp = pd.DataFrame([
#                     {'sdg': i + 1, **{
#                         str(years[0] + j): round(adjusted_budget * sdg['percent'] / 100 / periods, 2)
#                         for j in range(periods)
#                     }}
#                     for i, sdg in enumerate(allocation)
#                 ])
#             else:
#                 messages.error(request, "❌ Invalid manual budget input.")
#                 return redirect('budgets_page')

       
#         # Handle uploaded Excel file
#         elif 'upload_budget' in request.POST:
#             upload_form = Uploaded_Budget(request.POST, request.FILES)
#             if upload_form.is_valid():
#                 uploaded_file = request.FILES['government_expenditure']
#                 try:
#                     with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
#                         for chunk in uploaded_file.chunks():
#                             tmp.write(chunk)
#                         tmp_path = tmp.name

#                     # data_exp = pd.read_excel(tmp_path)
#                     data_exp = pd.read_excel(tmp_path)
#                     data_indi = pd.read_excel(indicators_path)

#                     data_exp = data_exp[data_exp.sdg.isin(data_indi.sdg.values)]
#                     data_exp = data_exp[data_exp.sdg.isin(data_indi[data_indi.instrumental==1].sdg.values)]

#                     years = [column_name for column_name in data_exp.columns if str(column_name).isnumeric()]
#                     periods = len(years)
#                     T = 1*periods  # Assuming T is the total number of periods, e.g., 4 years with 3 periods per year
#                     t = int(T/periods)

#                     new_rows = []
#                     for index, row in data_exp.iterrows():
#                         new_row = [row.sdg]
#                         for year in years:
#                             new_row+=[int(row[year]) for i in range(t)]
#                         new_rows.append(new_row)
                        
#                     df_exp = pd.DataFrame(new_rows, columns=['sdg']+list(range(T)))



#                     if 'sdg' not in data_exp.columns:
#                         messages.error(request, "❌ Uploaded file must have an 'sdg' column.")
#                         return redirect('budgets_page')

#                 except Exception as e:
#                     messages.error(request, f"❌ Failed to read uploaded file: {e}")
#                     return redirect('budgets_page')
#             else:
#                 messages.error(request, "❌ Invalid file upload.")
#                 return redirect('budgets_page')

       

#                 # --- Save budget sheet (template_expenditure) ---
#                 with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_budget:
#                     wb_budget = Workbook()
#                     ws_budget = wb_budget.active
#                     ws_budget.title = "template_expenditure"
#                     wb_budget.save(tmp_budget.name)
#                     request.session['budget_file_path'] = tmp_budget.name

#                 # --- Save relational table sheet ---
#                 with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_relation:
#                     wb_relation = Workbook()
#                     ws_relation = wb_relation.active
#                     ws_relation.title = "relational_table"
#                     wb_relation.save(tmp_relation.name)
#                     request.session['relation_file_path'] = tmp_relation.name

#                 messages.success(request, "☑️ Budget processed successfully.")
               

          
#     return render(request, 'budgets.html', {
#         'budget_form': budget_form,
#         'upload_form': upload_form,
#     })