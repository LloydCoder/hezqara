def test_supported_healthcare_interfaces_are_explicit():
    assert {'fhir','smart','payer_api','payment','messaging','document'} >= {'fhir','smart','payer_api'}
