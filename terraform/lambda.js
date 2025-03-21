const AWS = require('aws-sdk');
const ec2 = new AWS.EC2();

exports.handler = async (event) => {
  const instanceId = process.env.EC2_INSTANCE_ID; // <-- Obtener variable de entorno

  if (!instanceId) {
    console.error("No EC2 instance ID found in environment variables.");
    return;
  }

  const params = { InstanceIds: [instanceId] };

  try {
    await ec2.startInstances(params).promise();
    console.log(`EC2 Instance ${instanceId} started.`);
  } catch (error) {
    console.error("Error starting EC2 instance:", error);
  }
};
