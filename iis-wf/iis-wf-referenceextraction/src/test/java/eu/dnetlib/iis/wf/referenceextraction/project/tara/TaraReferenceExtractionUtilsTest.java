package eu.dnetlib.iis.wf.referenceextraction.project.tara;

import static eu.dnetlib.iis.wf.referenceextraction.project.tara.TaraReferenceExtractionUtils.buildDocumentMetadata;
import static eu.dnetlib.iis.wf.referenceextraction.project.tara.TaraReferenceExtractionUtils.runReferenceExtraction;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

import org.apache.spark.SparkFiles;
import org.apache.spark.sql.Dataset;
import org.apache.spark.sql.Row;
import org.apache.spark.sql.RowFactory;
import org.apache.spark.sql.avro.SchemaConverters;
import org.apache.spark.sql.types.StructType;
import org.junit.jupiter.api.Test;

import eu.dnetlib.iis.common.spark.TestWithSharedSparkSession;
import eu.dnetlib.iis.common.spark.pipe.PipeExecutionEnvironment;
import eu.dnetlib.iis.metadataextraction.schemas.DocumentText;
import eu.dnetlib.iis.referenceextraction.project.schemas.DocumentToProject;
import eu.dnetlib.iis.transformers.metadatamerger.schemas.ExtractedDocumentMetadataMergedWithOriginal;

public class TaraReferenceExtractionUtilsTest extends TestWithSharedSparkSession {

    @Test
    public void buildDocumentMetadataShouldRunProperly() {
        // given
        Dataset<Row> documentTextDF = createTextDataFrame(
                Arrays.asList(
                        createDocumentText("docId-1", "text-1"),
                        createDocumentText("docId-2", "text-2")
                ));
        Dataset<Row> extractedDocumentMetadataMergedWithOriginalDF = createMetaDataFrame(
                Arrays.asList(
                		 createDocumentMetadata("docId-1")
                ));

        // when
        Dataset<Row> resultDF = buildDocumentMetadata(documentTextDF, extractedDocumentMetadataMergedWithOriginalDF);

        // then
        assertEquals(TaraReferenceExtractionJob.DOCUMENT_METADATA_SCHEMA, resultDF.schema());

        List<Row> results = resultDF.collectAsList().stream()
                .sorted(Comparator.comparing(o -> o.getAs("id")))
                .collect(Collectors.toList());
        assertEquals(2, results.size());
        assertForDocumentMetadataRow(results.get(0), "docId-1", null, null, "text-1");
        assertForDocumentMetadataRow(results.get(1), "docId-2", null, null, "text-2");
    }

    @Test
    public void shouldRunReferenceExtraction() throws IOException {
        // given
        Dataset<Row> documentMetadataDF = spark().createDataFrame(
                Collections.singletonList(
                        createDocumentMetadata("id-1", "text-1")
                ),
                TaraReferenceExtractionJob.DOCUMENT_METADATA_SCHEMA);
        PipeExecutionEnvironment pipeExecutionEnvironment = () -> {
            Path scriptWithInputCheck = createTestScriptWithInputCheck();
            spark().sparkContext().addFile(scriptWithInputCheck.toString());
            return String.format("bash %s/%s", SparkFiles.getRootDirectory(),
                    scriptWithInputCheck.getFileName().toString());
        };

        // when
        Dataset<Row> resultDF = runReferenceExtraction(spark(), documentMetadataDF, pipeExecutionEnvironment);

        // then
        assertEquals(SchemaConverters.toSqlType(DocumentToProject.SCHEMA$).dataType().asNullable(),
                resultDF.schema().asNullable());

        List<Row> results = resultDF.collectAsList();
        assertEquals(1, results.size());
        Row row = results.get(0);
        assertForDocumentToProject(row, "docId-1", "projId-1", 1.0f);
    }

    private Dataset<Row> createTextDataFrame(List<DocumentText> inputList) {
    	List<Row> dataFrameList = new ArrayList<>(inputList.size());
    	for (DocumentText input : inputList) {
			dataFrameList.add(RowFactory.create(input.getId(), input.getText()));
    	}
    	return spark().createDataFrame(dataFrameList, 
    			(StructType) SchemaConverters.toSqlType(DocumentText.SCHEMA$).dataType());
    }
    
    private Dataset<Row> createMetaDataFrame(List<Row> inputList) {
    	return spark().createDataFrame(inputList, 
    			(StructType) SchemaConverters.toSqlType(ExtractedDocumentMetadataMergedWithOriginal.SCHEMA$).dataType());
    }
    
    private static DocumentText createDocumentText(String id, String text) {
        return DocumentText.newBuilder()
                .setId(id)
                .setText(text)
                .build();
    }

    private static Row createDocumentMetadata(String id) {
        return createDocumentMetadata(id, null);
    }

    private static Row createDocumentMetadata(String id, String text) {
        return RowFactory.create(id, null, null, text);
    }

    private static Path createTestScriptWithInputCheck() throws IOException {
        String content = String.join(System.getProperty("line.separator"),
                "#!/bin/bash",
                "read in",
                "test ${in:0:1} == '{' -a ${in: -1} == '}' && echo '{\"documentId\":\"docId-1\",\"projectId\":\"projId-1\",\"confidenceLevel\":1,\"textsnippet\":null}'"
        );
        return Files.write(Files.createTempFile(null, "sh"), content.getBytes());
    }

    private static void assertForDocumentMetadataRow(Row row,
                                                     String id,
                                                     String title,
                                                     String abstract$,
                                                     String text) {
        assertEquals(id, row.getAs("id"));
        assertEquals(title, row.getAs("title"));
        assertEquals(abstract$, row.getAs("abstract"));
        assertEquals(text, row.getAs("text"));
    }

    private static void assertForDocumentToProject(Row row,
                                                   String documentId,
                                                   String projectId,
                                                   Float confidenceLevel) {
        assertEquals(documentId, row.getAs("documentId"));
        assertEquals(projectId, row.getAs("projectId"));
        assertEquals(confidenceLevel, row.<Float>getAs("confidenceLevel"), 1e-3);
        assertNull(row.getAs("textsnippet"));
    }
}