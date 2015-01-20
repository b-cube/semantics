NutchDocument
	NutchDocument describedBy ServiceDescriptionDocument

	ServiceDescriptionDocument
		ServiceDescriptionDocument has name "Search For Level 1 and Atmosphere Products"
		ServiceDescriptionDocument has endpoint "opensearch-nasa.xml"
		ServiceDescriptionDocument has attribution "nasa.gov"
		ServiceDescriptionDocument has description "Use MODAPS Web Services to search for various MODIS related data products"
		ServiceDescriptionDocument has namespace "http://a9.com/-/spec/opensearch/1.1/"


		ServiceDescriptionDocument hasServiceProfile [ServiceProfile]
			ServiceProfile has version "1.1"
			ServiceProfile has namespace "http://a9.com/-/spec/opensearch/1.1/"
			ServiceProfile has profileNameSpace "http://a9.com/-/spec/opensearch/1.1/"
			ServiceProfile has profileType "OpenSearch"

			ServiceProfile hasParameters [ServiceParameter:geo:box]
				ServiceParameter has namespace "http://a9.com/-/opensearch/extensions/geo/1.0/"
				ServiceParameter has parameterFormat "geo:box ~ west, south, east, north"
				ServiceParameter has parameterRange ""
				ServiceParameter has parameterType "geo"
			ServiceProfile hasParameters [ServiceParameter:time:start]
				ServiceParameter has namespace "http://a9.com/-/opensearch/extensions/time/1.0/"
				ServiceParameter has parameterFormat "YYYY-MM-DDTHH:mm:ssZ"
				ServiceParameter has parameterRange ""
				ServiceParameter has parameterType "time"
			ServiceProfile hasParameters [ServiceParameter:time:end]
				ServiceParameter has namespace "http://a9.com/-/opensearch/extensions/time/1.0/"
				ServiceParameter has parameterFormat "YYYY-MM-DDTHH:mm:ssZ"
				ServiceParameter has parameterRange ""
				ServiceParameter has parameterType "time"
			ServiceProfile hasParameters [ServiceParameter:MODAPSParameters:dayNightBoth]
				ServiceParameter has namespace ""
				ServiceParameter has parameterFormat ""
				ServiceParameter has parameterRange ""
				ServiceParameter has parameterType "generic"
			ServiceProfile hasParameters [ServiceParameter:MODAPSParameters:coordsOrTiles]
				ServiceParameter has namespace ""
				ServiceParameter has parameterFormat ""
				ServiceParameter has parameterRange ""
				ServiceParameter has parameterType "generic"
			ServiceProfile hasParameters [ServiceParameter:MODAPSParameters:products]
				ServiceParameter has namespace ""
				ServiceParameter has parameterFormat ""
				ServiceParameter has parameterRange ""
				ServiceParameter has parameterType "generic"
			ServiceProfile hasParameters [ServiceParameter:MODAPSParameters:collection]
				ServiceParameter has namespace ""
				ServiceParameter has parameterFormat ""
				ServiceParameter has parameterRange ""
				ServiceParameter has parameterType "generic"
