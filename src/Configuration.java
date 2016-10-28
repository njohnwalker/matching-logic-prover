import java.util.ArrayList;
import java.util.List;

/**
 * Created by shell on 10/27/16.
 */
public class Configuration {
    private String constructor = null;
    private List<Configuration> subConfigurations = new ArrayList<>();

    public Configuration(String constructor) {
        this.constructor = constructor;
    }

    public void addSubConfiguration(Configuration subConfiguration){
        subConfigurations.add(subConfiguration);
    }

    public String getConstructor() {
        return constructor;
    }
    public List<Configuration> getSubConfigurations() {
        return subConfigurations;
    }

    /**
     * Transform the object to Stirng object.
     * This method is automatically generated by IntelliJ.
     * @return A String object that represents the configuration.
     */
    @Override
    public String toString() {
        return "Configuration{" +
                "constructor='" + constructor + '\'' +
                ", subConfigurations=" + subConfigurations +
                '}';
    }
}
