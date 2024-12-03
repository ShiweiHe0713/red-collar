package com.company.red_collar;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.influxdb.client.WriteApiBlocking;
import com.influxdb.client.domain.WritePrecision;
import com.influxdb.client.write.Point;
import org.kie.api.runtime.KieSession;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;

@Service
public class OrderReceiver {

    private final KieSession kieSession;
    private final ObjectMapper objectMapper = new ObjectMapper(); // For JSON parsing
    private final WriteApiBlocking writeApiBlocking;

    @Autowired
    public OrderReceiver(KieSession kieSession, WriteApiBlocking writeApiBlocking) {
        this.kieSession = kieSession;
        this.writeApiBlocking = writeApiBlocking;
    }

    @RabbitListener(queues = "order_queue", concurrency = "5-20")
    public void receiveOrder(String orderMessage) {
        try {
            // Deserialize the order JSON
            Map<String, Object> order = objectMapper.readValue(orderMessage, Map.class);

            // Extract order details
            String orderId = (String) order.get("order_id");
            String fullName = (String) ((Map<String, Object>) order.get("customer")).get("name");
            String[] nameParts = fullName.split(" ");
            String firstName = nameParts.length > 0 ? nameParts[0] : "";
            String lastName = nameParts.length > 1 ? nameParts[1] : "";
            String itemStatus = "0.Received";

            for (Map<String, Object> item : (Iterable<Map<String, Object>>) order.get("items")) {
                String type = (String) item.get("type");
                String size = (String) item.get("size");
                String color = (String) item.get("color");
                int quantity = (int) item.get("quantity");

                // Write each item instance to InfluxDB
                writeOrderToInfluxDB(orderId, firstName, lastName, type, size, color, quantity, itemStatus);

                // Start the process
                for (int i = 1; i <= quantity; i++) {
                    // Prepare process variables
                    Map<String, Object> processVariables = Map.of(
                        "orderId", orderId,
                        "firstName", firstName,
                        "lastName", lastName,
                        "itemType", type,
                        "itemSize", size,
                        "itemColor", color,
                        "itemIndex", i,
                        "totalQuantity", quantity
                    );

                    // Start the process 
                    kieSession.startProcess("ClothingProcess", processVariables);
                    System.out.println("Started process for Order ID: " + orderId + ", Customer: " + firstName + " " + lastName + ", Item: " + type + "-" + size + "-" + color + "-" + i);
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    // Write data to InfluxDB
    private void writeOrderToInfluxDB(String orderId, String firstName, String lastName, String itemType, String itemSize, String itemColor, int totalQuantity, String itemStatus) {
        Point point = Point.measurement("order_measurement")
            .addTag("order_id", orderId)
            .addField("first_name", firstName)
            .addField("last_name", lastName)
            .addField("item_type", itemType)
            .addField("item_size", itemSize)
            .addField("item_color", itemColor)
            .addField("total_quantity", totalQuantity)
            .addField("item_status", itemStatus)
            .time(Instant.now(), WritePrecision.MS);

        // Write to InfluxDB
        writeApiBlocking.writePoint(point);
    }
}
