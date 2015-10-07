package eu.dnetlib.iis.workflows.transformers.metricsprimary;

import org.junit.Test;
import org.junit.experimental.categories.Category;

import eu.dnetlib.iis.IntegrationTest;
import eu.dnetlib.iis.core.AbstractOozieWorkflowTestCase;

/**
 * 
 * @author Dominika Tkaczyk
 *
 */
@Category(IntegrationTest.class)
public class WorkflowTest extends AbstractOozieWorkflowTestCase {

    @Test
	public void testWorkflow() throws Exception {
        testWorkflow("eu/dnetlib/iis/workflows/transformers/metricsprimary/sampledataproducer");
    }

}
