pip install .

pushd venvpy/lib/python3.7/site-packages
zip -r9 base_function.zip .
popd

cp venvpy/lib/python3.7/site-packages/base_function.zip lambdas/submit_job/function.zip
cp venvpy/lib/python3.7/site-packages/base_function.zip lambdas/upload_results_to_datasets/function.zip
cp venvpy/lib/python3.7/site-packages/base_function.zip lambdas/check_datasets_saved/function.zip
cp venvpy/lib/python3.7/site-packages/base_function.zip lambdas/check_new_areas/function.zip
cp venvpy/lib/python3.7/site-packages/base_function.zip lambdas/update_new_area_statuses/function.zip

pushd lambdas/submit_job
zip -g function.zip function.py
popd

pushd lambdas/upload_results_to_datasets
zip -g function.zip function.py
popd

pushd lambdas/check_datasets_saved
zip -g function.zip function.py
popd

pushd lambdas/check_new_areas
zip -g function.zip function.py
popd

pushd lambdas/update_new_area_statuses
zip -g function.zip function.py
popd

rm venvpy/lib/python3.7/site-packages/base_function.zip