using UnityEngine.UI;
using System.Collections.Generic;
using UnityEngine;
using System;


public class SpriteControllerForObjectDiscrimination : MonoBehaviour
{
    private bool shownOnScreen;

    // Start is called before the first frame update
    void Start()
    {
        this.gameObject.SetActive(false);

        EventManager.Instance.onUpdatedMotion.AddListener(DoUpdate);
        EventManager.Instance.onUpdateScreensOn.AddListener(DoScreensSelection);
        EventManager.Instance.onUpdateTargetTrapOpacity.AddListener(DoShapeOpacityUpdate);
        EventManager.Instance.onUpdateCueOpacity.AddListener(DoCueOpacityUpdate);

        shownOnScreen = false;
    }


    void DoScreensSelection(string screens)
    {
        //Debug.Log(string.Format("Screens for {0} are set to {1}", transform.name, screens));
        if (transform.name.Contains("Right") && (screens == "Both" || screens == "Right"))
        {
            shownOnScreen = true;
        }
        if (transform.name.Contains("Front") && (screens == "Both" || screens == "Front"))
        {
            shownOnScreen = true;
        }

        //if (transform.name.Contains("Cue"))
        //{
        //    EventManager.Instance.onCueAnimate.Invoke();
        //}
    }

    void DoShapeOpacityUpdate(string _opacity)
    {
        //Debug.Log(string.Format("Opacity for {0} is set to {1}", transform.name, _opacity));
        if (transform.name.Contains("Line") || transform.name.Contains("Square") || transform.name.Contains("Circle"))
        {
            DoOpacityUpdate(_opacity);
        }
    }

    void DoCueOpacityUpdate(string _opacity)
    {
        //Debug.Log(_opacity);
        if (transform.name.Contains("Cue"))
        {
            DoOpacityUpdate(_opacity);
        }
    }

    void DoOpacityUpdate(string _opacity)
    {
        float opacity = float.Parse(_opacity);
        Color current_color = transform.GetComponent<Image>().color;
        transform.GetComponent<Image>().color = new Color(current_color.r, current_color.g, current_color.b, opacity);
    }

    List<float[]> GetAllSpritesStates(string sprites_message)
    {
        string[] sprites_messages = sprites_message.Split(',');
        List<float[]> sprites_states = new List<float[]>();
        foreach (string sm in sprites_messages)
        {            
            string str_after_equals = sm.Substring(sm.IndexOf("=")).Substring(1);
            float[] state = new float[2];
            state[0] = float.Parse(str_after_equals.Substring(0, str_after_equals.IndexOf("R")));
            state[1] = float.Parse(str_after_equals.Substring(str_after_equals.IndexOf("R")).Substring(1));
            sprites_states.Add(state);
            //Debug.Log(string.Format("{0} || {1}", state[0], state[1]));
        }
        
        return sprites_states;
    }

    float[] GetStateForThisSprite(List<float[]> sprites_states)
    {
        int sprite_type = new int();

        if (transform.name.Contains("Cue")) sprite_type = 0;
        if (transform.name.Contains("Line"))
        {
            if (transform.name.Contains("Checkered")) sprite_type = 1;
            if (transform.name.Contains("White")) sprite_type = 2;
            if (transform.name.Contains("Black")) sprite_type = 3;
        }
        if (transform.name.Contains("Circle"))
        {
            if (transform.name.Contains("Checkered")) sprite_type = 4;
            if (transform.name.Contains("White")) sprite_type = 5;
            if (transform.name.Contains("Black")) sprite_type = 6;
        }
        if (transform.name.Contains("Square"))
        {
            if (transform.name.Contains("Checkered")) sprite_type = 7;
            if (transform.name.Contains("White")) sprite_type = 8;
            if (transform.name.Contains("Black")) sprite_type = 9;
        }

        return sprites_states[sprite_type];
    }

    void HideOrShow(float state_pos)
    {
        this.gameObject.SetActive(false);
        //Debug.Log(string.Format("{0} is {1} and screen is {2}", transform.name, state_pos, shownOnScreen));
        if (state_pos != 0f && shownOnScreen)
        {
            this.gameObject.SetActive(true);
            //Debug.Log(string.Format("{0} is made Active", transform.name));
        }
    }

    void DoAnimationIfCue(float state)
    {
        //If the sprite is the Cue and it is shown on screen and the state sent by the Heron node is 1 then animate it (that means that states != 1 will not do anything except 0 which will hide it)
        //Debug.Log(state);
        if (transform.name.Contains("Cue") && shownOnScreen && state == 1f)
        {
           // Debug.Log("Anim invoked");
            if (transform.name.Contains("Right"))
                EventManager.Instance.onCueAnimate.Invoke("Right");
            if (transform.name.Contains("Front"))
                EventManager.Instance.onCueAnimate.Invoke("Front");
        }
    }

    void ChangeTransformIfNotCue(float[] state)
    {
        float state_pos = state[0];
        float state_rot = state[1];
        if (!transform.name.Contains("Cue") && shownOnScreen)
        {
            if (transform.name.Contains("Right"))
            {
                transform.rotation = Quaternion.Euler(Vector3.forward * 90);
                int starting_position = 0;
                transform.localPosition = new Vector3(transform.localPosition.x, starting_position + state_pos, transform.localPosition.z);
            }
            else
            {
                int starting_position = -972;
                transform.localPosition = new Vector3(starting_position + state_pos, transform.localPosition.y, transform.localPosition.z);
            }
            transform.rotation = Quaternion.Euler(new Vector3(0, 0, transform.rotation.z + state_rot));

        }
    }

    void DoUpdate(string sprites_message)
    {
        List<float[]> sprites_states = GetAllSpritesStates(sprites_message);

        float[] state = GetStateForThisSprite(sprites_states);

        ChangeTransformIfNotCue(state);

        HideOrShow(state[0]);

        DoAnimationIfCue(state[0]);

    }
}
